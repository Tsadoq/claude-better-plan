#!/usr/bin/env python3
"""Render the Claude-native source tree into per-host builds under ``dist/<host>/``.

``render`` writes one build from one ``HostProfile``; ``diff_build`` is the one
definition of whether a committed build is fresh. The CLI renders every profile
in ``hosts/`` (or the named ones), or with ``--check`` reports stale builds.
Never hand-edit ``dist/``: change the source or the profile and re-run this.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import shutil
import sys
import tempfile
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from hosts.profile import ROOT, Frontmatter, HostProfile  # noqa: E402

# What a build copies from the source root; anything else (tests, docs, CI,
# manifests) stays Claude-side. A missing entry is skipped.
SOURCE_ENTRIES = ("skills", "agents", "lib", "PLAN.md")
# Directory names never copied into, nor compared within, a build. Every walk
# and copy below goes through _walk or _ignore_excluded, so this is the only list.
EXCLUDED_DIRS = frozenset({"tests", "__pycache__"})
# Splits an overlay file name into its target markdown path and its heading.
OVERLAY_SEP = ".md#"

_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_HEADING_RE = re.compile(r"^(#{1,6}) \S")
_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):(.*)$")


class RenderError(Exception):
    """The profile and the source disagree, so no correct build can be written."""


def render(source_root: Path, profile: HostProfile, out: Path) -> None:
    """Write ``profile``'s build of ``source_root`` to ``out``, replacing anything there.

    Markdown files get, in order: the frontmatter transform, overlays, the token
    map, and (for each ``SKILL.md``) the HOST.md pointer as the first body line.
    Every other file is copied byte-for-byte. Then ``extra_files`` are copied and
    ``hosts/<name>/HOST.md`` is written at the build root.

    Raises ``RenderError`` when an overlay's file or heading is missing from the
    source, or a HOST.md or extra file does not exist.
    """
    source_root = source_root.resolve()
    out = out.resolve()
    if out == source_root or out in source_root.parents:
        raise RenderError(f"refusing to replace {out}: it contains the source tree")
    rules = _Rules.of(profile)
    host_md = source_root / "hosts" / profile.name / "HOST.md"
    if not host_md.is_file():
        raise RenderError(f"profile {profile.name!r} has no {host_md}")

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    unapplied = dict(rules.overlays)
    for rel in _source_files(source_root):
        target = out / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if rel.suffix != ".md":
            shutil.copy(source_root / rel, target)
            continue
        overlays = {h: o for (md, h), o in rules.overlays.items() if md == rel.as_posix()}
        for heading in overlays:
            del unapplied[(rel.as_posix(), heading)]
        text = (source_root / rel).read_text(encoding="utf-8")
        target.write_text(_render_markdown(text, rel, rules, overlays, profile.name), encoding="utf-8")
    if unapplied:
        (md, heading), overlay = next(iter(unapplied.items()))
        raise RenderError(f"overlay {overlay.path}: {md} is not in the build, so {heading!r} cannot apply")

    for build_rel, source_rel in rules.extra_files.items():
        _copy_verbatim(source_root / source_rel, out / build_rel)
    shutil.copyfile(host_md, out / "HOST.md")


def host_pointer(host: str) -> str:
    """The line every ``SKILL.md`` in ``host``'s build opens its body with."""
    return f"This build targets {host}. Read {ROOT}/HOST.md once before following any step below."


def diff_build(expected: Path, actual: Path) -> list[str]:
    """The relative paths that differ between two build trees, sorted.

    A path differs when it exists on one side only or its bytes differ. An empty
    list means ``actual`` is a fresh copy of ``expected``. ``EXCLUDED_DIRS`` are
    ignored on both sides; a missing tree counts as empty.
    """
    left, right = _tree_files(expected), _tree_files(actual)
    differing = left ^ right
    differing |= {p for p in left & right if (expected / p).read_bytes() != (actual / p).read_bytes()}
    return sorted(differing)


@dataclass(frozen=True)
class _Overlay:
    path: Path
    text: str


@dataclass(frozen=True)
class _Rules:
    """A profile with its ``extends`` chain folded in, root ancestor first."""

    tokens: tuple[tuple[re.Pattern[str], str], ...]
    drop_frontmatter: frozenset[str]
    agent_frontmatter: Callable[[Frontmatter], Frontmatter] | None
    overlays: dict[tuple[str, str], _Overlay]  # (markdown path, heading) -> overlay
    extra_files: dict[str, str]

    @staticmethod
    def of(profile: HostProfile) -> _Rules:
        chain: list[HostProfile] = []
        node: HostProfile | None = profile
        while node is not None:
            chain.append(node)
            node = node.extends
        tokens: list[tuple[re.Pattern[str], str]] = []
        drop: set[str] = set()
        agent: Callable[[Frontmatter], Frontmatter] | None = None
        overlays: dict[tuple[str, str], _Overlay] = {}
        extra: dict[str, str] = {}
        for p in reversed(chain):  # each child overrides what its ancestors set
            tokens += [(re.compile(pattern), replacement) for pattern, replacement in p.tokens]
            drop |= set(p.drop_frontmatter)
            agent = p.agent_frontmatter or agent
            if p.overlays_dir is not None:
                overlays.update(_read_overlays(p.overlays_dir))
            extra.update(p.extra_files)
        return _Rules(tuple(tokens), frozenset(drop), agent, overlays, extra)


def _read_overlays(overlays_dir: Path) -> dict[tuple[str, str], _Overlay]:
    found: dict[tuple[str, str], _Overlay] = {}
    for path in sorted(p for p in overlays_dir.rglob("*") if p.is_file()):
        name = path.relative_to(overlays_dir).as_posix()
        md, sep, heading = name.partition(OVERLAY_SEP)
        if not sep or not heading.endswith(".md"):
            raise RenderError(f"overlay {path}: name is not '<path>.md#<heading>.md'")
        found[(md + ".md", heading.removesuffix(".md"))] = _Overlay(path, path.read_text(encoding="utf-8"))
    return found


def _source_files(source_root: Path) -> Iterator[Path]:
    """Every file a build copies, relative to ``source_root``, in a stable order."""
    for entry in SOURCE_ENTRIES:
        top = source_root / entry
        if top.is_file():
            yield Path(entry)
        elif top.is_dir():
            yield from (p.relative_to(source_root) for p in _walk(top))


def _walk(top: Path) -> Iterator[Path]:
    """Every file under ``top`` outside ``EXCLUDED_DIRS``, in a stable order."""
    for dirpath, dirnames, filenames in os.walk(top):
        dirnames[:] = sorted(set(dirnames) - set(_ignore_excluded(dirpath, dirnames)))
        yield from (Path(dirpath) / f for f in sorted(filenames))


def _ignore_excluded(dirpath: str, names: list[str]) -> list[str]:
    """The ``EXCLUDED_DIRS`` among ``names``; shaped as a ``shutil.copytree`` ignore."""
    return [n for n in names if n in EXCLUDED_DIRS and os.path.isdir(os.path.join(dirpath, n))]


def _tree_files(top: Path) -> set[str]:
    return {p.relative_to(top).as_posix() for p in _walk(top)} if top.is_dir() else set()


def _copy_verbatim(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target, ignore=_ignore_excluded)
    elif source.is_file():
        shutil.copy(source, target)
    else:
        raise RenderError(f"extra file {source} does not exist")


def _render_markdown(
    text: str, rel: Path, rules: _Rules, overlays: dict[str, _Overlay], host: str
) -> str:
    """The split happens once here; each step below sees only the part it rewrites."""
    frontmatter, body = _split_frontmatter(text)
    if frontmatter is not None:
        frontmatter = _transform_frontmatter(frontmatter, rules, is_agent=rel.parts[0] == "agents")
    for heading, overlay in overlays.items():
        body = _replace_section(body, heading, overlay, rel)
    for pattern, replacement in rules.tokens:
        frontmatter = None if frontmatter is None else pattern.sub(replacement, frontmatter)
        body = pattern.sub(replacement, body)
    if rel.name == "SKILL.md":  # after the tokens, so no token map can rewrite the pointer
        gap = "" if frontmatter is None else "\n"  # a blank line after the closing fence
        body = gap + host_pointer(host) + "\n" + ("\n" + body.lstrip("\n") if body.strip() else "")
    return _join_frontmatter(frontmatter, body)


def _split_frontmatter(text: str) -> tuple[str | None, str]:
    """``(frontmatter lines without the --- fences, body)``, or ``(None, text)``.

    The frontmatter keeps its last newline, so ``_join_frontmatter`` undoes this.
    """
    if not text.startswith("---\n"):
        return None, text
    # Search from index 3, the newline ending the opening fence, so an empty
    # frontmatter ("---\n---\n") still finds its closing fence.
    end = text.find("\n---\n", 3)
    if end == -1:
        return None, text
    return text[4 : end + 1], text[end + 5 :]


def _join_frontmatter(frontmatter: str | None, body: str) -> str:
    """The inverse of ``_split_frontmatter``."""
    return body if frontmatter is None else f"---\n{frontmatter}---\n{body}"


def _transform_frontmatter(frontmatter: str, rules: _Rules, *, is_agent: bool) -> str:
    """Drop the profile's keys, then (for an agent) apply its agent mapping."""
    comments: dict[str, list[str]] = {}
    values: Frontmatter = {}
    pending: list[str] = []
    key = ""
    for line in frontmatter.splitlines():
        match = _KEY_RE.match(line)
        if match:
            key = match.group(1)
            comments[key], pending = pending, []
            values[key] = match.group(2).lstrip(" ")
        elif key and line.startswith((" ", "\t")):
            values[key] += "\n" + line
        else:  # a comment or blank line, kept with the key below it
            pending.append(line)
    values = {k: v for k, v in values.items() if k not in rules.drop_frontmatter}
    if is_agent and rules.agent_frontmatter is not None:
        values = rules.agent_frontmatter(values)
    lines: list[str] = []
    for k, v in values.items():
        lines += comments.get(k, [])
        lines.append(f"{k}:" + ("" if not v or v.startswith("\n") else " ") + v)
    lines += pending
    return "".join(line + "\n" for line in lines)


def _replace_section(body: str, heading: str, overlay: _Overlay, rel: Path) -> str:
    """Swap the section under ``heading`` (to the next heading of its level or higher) for ``overlay``."""
    lines = body.splitlines(keepends=True)
    level = len(heading) - len(heading.lstrip("#"))
    starts: list[int] = []
    end = len(lines)
    in_fence = False
    for i, line in enumerate(lines):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
        if in_fence or not _HEADING_RE.match(line):
            continue
        if line.rstrip() == heading:
            starts.append(i)
        elif starts and end == len(lines) and i > starts[0]:
            if len(line) - len(line.lstrip("#")) <= level:
                end = i
    if len(starts) != 1:
        found = "not found" if not starts else f"found {len(starts)} times"
        raise RenderError(f"overlay {overlay.path}: heading {heading!r} {found} in {rel}")
    replacement = overlay.text.rstrip("\n")
    if replacement:
        replacement += "\n\n" if end < len(lines) else "\n"
    return "".join(lines[: starts[0]]) + replacement + "".join(lines[end:])


def _profiles(repo: Path) -> dict[str, HostProfile]:
    """Every ``<repo>/hosts/<name>/`` package's ``PROFILE``, by name, loaded as ``hosts.<name>``."""
    found: dict[str, HostProfile] = {}
    for package in sorted((repo / "hosts").glob("*/__init__.py")):
        name = package.parent.name
        module_name = f"hosts.{name}"
        spec = importlib.util.spec_from_file_location(
            module_name, package, submodule_search_locations=[str(package.parent)]
        )
        if spec is None or spec.loader is None:
            raise RenderError(f"{package} cannot be imported")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module  # so a sibling profile can `from hosts.<name> import PROFILE`
        spec.loader.exec_module(module)
        profile = getattr(module, "PROFILE", None)
        if not isinstance(profile, HostProfile):
            raise RenderError(f"{package} defines no PROFILE")
        found[name] = profile
    return found


def main(argv: list[str] | None = None, *, repo: Path = REPO) -> int:
    """Render (or with ``--check``, compare) ``repo``'s builds; exit status 1 means a build is stale."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--check", action="store_true", help="report stale builds instead of writing")
    parser.add_argument("hosts", nargs="*", help="profiles to render (default: every one in hosts/)")
    args = parser.parse_args(argv)
    profiles = _profiles(repo)
    unknown = sorted(set(args.hosts) - set(profiles))
    if unknown:
        parser.error(f"no profile for {', '.join(unknown)}; known: {', '.join(profiles) or 'none'}")
    stale: list[str] = []
    with tempfile.TemporaryDirectory() as scratch:
        for name in args.hosts or list(profiles):
            committed = repo / "dist" / name
            out = Path(scratch) / name if args.check else committed
            render(repo, profiles[name], out)
            if args.check:
                stale += [f"dist/{name}/{p}" for p in diff_build(committed, out)]
    for path in stale:
        print(path)
    if stale:
        command = " ".join(["python3 tools/render_hosts.py", *args.hosts])
        print(f"stale builds: run {command}", file=sys.stderr)
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
