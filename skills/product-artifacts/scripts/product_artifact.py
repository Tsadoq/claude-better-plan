#!/usr/bin/env python3
"""Query and mutate core for the docs/product/<slug>/ artifact family.

Usage:
    product_artifact.py --exists --slug <slug> --product-dir <dir>
    product_artifact.py --resolve-slug --slug <slug> --product-dir <dir>
    product_artifact.py --check-freshness --product-dir <dir> [--slug <slug>]
    product_artifact.py --ensure-folder --slug <slug> --product-dir <dir>

`--exists`, `--resolve-slug` and `--check-freshness` each answer a caller's
question about chain state in a single call and are read-only: neither
creates a folder or a member file. `--ensure-folder` is the package's one
writing entry point: it creates the slug folder (parents, exist-ok) and
then regenerates the product index unconditionally, so a folder without its
index row is never a state a caller can observe (see
`references/artifact-family.md`'s `## Re-run behaviour`).

The member chain and its provenance/staleness rules are published in
`skills/product-artifacts/references/artifact-family.md`; this module is
that contract's only implementation and must not drift from it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

# Plugin-root lib/ carries the slug rules shared with every artifact family;
# see lib/artifact_common.py's module docstring for why this is a sys.path
# bootstrap rather than a package import.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
import artifact_common  # noqa: E402

# The closed five-member chain, in chain order. Mirrors the `## Members`
# table in artifact-family.md; that table is the published source of truth
# and this tuple must not drift from it.
MEMBERS: tuple[str, ...] = (
    "brief.md",
    "discovery.md",
    "requirements.md",
    "spec.md",
    "roadmap.md",
)

# Each member after the first, mapped to its immediate predecessor.
UPSTREAM: dict[str, str] = {member: MEMBERS[i - 1] for i, member in enumerate(MEMBERS) if i > 0}

# The product family has no legacy flat form, unlike docs/plans/, so slug
# collision checks pass no extra_suffixes.
_NO_EXTRA_SUFFIXES: tuple[str, ...] = ()

# The published provenance line, matched anywhere in a member's text (see
# artifact-family.md's `## Provenance`): a bare upstream filename and exactly
# 40 lowercase hex characters, tolerant of surrounding whitespace on the line
# but anchored at both ends so a truncated sha or trailing garbage fails to
# match rather than passing silently.
PROVENANCE_RE = re.compile(
    r"^[ \t]*\*\*Derived from\*\*:[ \t]*(\S+)[ \t]+\(([0-9a-f]{40})\)[ \t]*$",
    re.MULTILINE,
)


def blob_sha(data: bytes) -> str:
    """The git blob object id for `data`: SHA-1 over the header
    `blob <byte length>\\0` followed by the bytes themselves. Pure standard
    library; needs no repository, no commit and no `git` executable."""
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()  # noqa: S324 -- git's own object id algorithm, not a security use


def member_state(folder: Path, member: str) -> str:
    """One of `fresh`, `stale`, `unresolvable` or `absent` for `member` in
    `folder`, per artifact-family.md's `## Staleness`.

    `absent` when the member file is missing. The first member in `MEMBERS`
    has no upstream, so it is `fresh` when present, never `stale` or
    `unresolvable`. For every other member: `unresolvable` when the
    provenance line is missing or malformed, when it names a member other
    than this member's chain predecessor, or when that predecessor's file
    does not exist; `stale` when the recorded sha differs from `blob_sha`
    over the predecessor's current bytes; `fresh` otherwise.

    The predecessor is read as bytes, so a symlinked member hashes its
    target's bytes rather than the link text -- a documented limit, not
    special-cased here (see artifact-family.md and the module docstring).
    """
    path = folder / member
    if not path.exists():
        return "absent"

    upstream_name = UPSTREAM.get(member)
    if upstream_name is None:
        return "fresh"

    text = path.read_text(encoding="utf-8", errors="replace")
    match = PROVENANCE_RE.search(text)
    if match is None or match.group(1) != upstream_name:
        return "unresolvable"

    upstream_path = folder / upstream_name
    if not upstream_path.exists():
        return "unresolvable"

    upstream_bytes = upstream_path.read_bytes()
    if blob_sha(upstream_bytes) != match.group(2):
        return "stale"
    return "fresh"


def member_presence(folder: Path) -> dict[str, bool]:
    """An ordered mapping of member filename to whether it exists in
    `folder`, in chain order.

    Iterates `MEMBERS` and stats each path directly, so no caller ever globs
    `folder` itself to discover what is there.
    """
    return {member: (folder / member).exists() for member in MEMBERS}


def _absent_members() -> dict[str, bool]:
    """The all-absent member map, used when a slug is invalid and no folder
    can be safely constructed for it."""
    return dict.fromkeys(MEMBERS, False)


def cmd_exists(raw_slug: str, product_dir: Path) -> dict[str, Any]:
    slug = artifact_common.normalise_slug(raw_slug)
    valid = artifact_common.is_valid_slug(slug)

    if valid:
        folder = product_dir / slug
        present = folder.exists()
        members = member_presence(folder)
    else:
        present = False
        members = _absent_members()

    return {
        "slug": slug,
        "valid": valid,
        "present": present,
        "members": members,
    }


def cmd_resolve_slug(raw_slug: str, product_dir: Path) -> dict[str, Any]:
    slug = artifact_common.normalise_slug(raw_slug)
    valid = artifact_common.is_valid_slug(slug)

    if valid:
        folder = product_dir / slug
        collision = artifact_common.slug_taken(product_dir, slug, _NO_EXTRA_SUFFIXES)
        auto_v_suffix = (
            artifact_common.next_v_suffix(product_dir, slug, _NO_EXTRA_SUFFIXES)
            if collision
            else None
        )
        members = member_presence(folder)
        path: str | None = str(folder)
    else:
        collision = False
        auto_v_suffix = None
        members = _absent_members()
        path = None

    return {
        "input": raw_slug,
        "slug": slug,
        "valid": valid,
        "path": path,
        "collision": collision,
        "auto_v_suffix": auto_v_suffix,
        "members": members,
        "product_dir": str(product_dir),
    }


def cmd_check_freshness(raw_slug: str | None, product_dir: Path) -> dict[str, Any]:
    """One entry per slug, each an ordered `members` map of `member_state`
    results in chain order.

    A single entry for the named slug when `raw_slug` is given -- its folder
    need not exist; a missing folder yields all five members `absent`, which
    falls out of `member_state`'s own presence check with no special case
    here. One entry per existing slug folder under `product_dir`, sorted by
    slug name, when `raw_slug` is absent. Either way this never raises: the
    only non-zero exit this script owns is its own inability to run.
    """
    if raw_slug is not None:
        slug_names = [artifact_common.normalise_slug(raw_slug)]
    elif product_dir.exists():
        slug_names = sorted(p.name for p in product_dir.iterdir() if p.is_dir())
    else:
        slug_names = []

    entries = [
        {
            "slug": name,
            "members": {member: member_state(product_dir / name, member) for member in MEMBERS},
        }
        for name in slug_names
    ]

    return {
        "product_dir": str(product_dir),
        "slug": raw_slug,
        "entries": entries,
    }


# The index README's file name and marker pair, module-level so both the
# writer here and a future reader agree on one literal each.
PRODUCT_README_NAME = "README.md"
_PRODUCT_MARKERS = artifact_common.markers("product")


def _chain_progress(folder: Path) -> str:
    """The chain-order name of the furthest member present in `folder`, or
    `none` when the folder has no member written yet."""
    progress = "none"
    for member in MEMBERS:
        if (folder / member).exists():
            progress = member
    return progress


def regenerate_product_index(product_dir: Path) -> Path:
    """Regenerate `product_dir`'s README.md between the `product` markers.

    One row per existing slug folder, sorted by slug: a chain-progress cell
    naming the furthest member present and a stale-member count from
    `member_state`. Every cell derives from folder content, never from
    mtime, so a merge conflict in the README is resolved by regenerating
    rather than hand-editing. Called unconditionally by `--ensure-folder` on
    every invocation, so a re-run repairs an index that was lost or
    hand-edited.
    """
    slugs = (
        sorted(p.name for p in product_dir.iterdir() if p.is_dir())
        if product_dir.exists()
        else []
    )

    rows = []
    for slug in slugs:
        folder = product_dir / slug
        progress = _chain_progress(folder)
        stale = sum(1 for member in MEMBERS if member_state(folder, member) == "stale")
        rows.append(f"| {slug} | {progress} | {stale} |")

    region = artifact_common.build_table_region(
        _PRODUCT_MARKERS, ["Slug", "Chain progress", "Stale members"], rows
    )

    readme = product_dir / PRODUCT_README_NAME
    text = readme.read_text() if readme.exists() else "# Product artifacts\n"
    text = artifact_common.splice_region(text, _PRODUCT_MARKERS, region)
    readme.write_text(text)
    return readme


def cmd_ensure_folder(raw_slug: str, product_dir: Path) -> dict[str, Any]:
    """Create `<product_dir>/<slug>` when absent, then regenerate the
    product index unconditionally.

    `created` is true only when the folder itself did not exist before this
    call. The index is written every time regardless of `created`, so a
    folder without its index row is a state this call never leaves behind
    (see artifact-family.md's `## Re-run behaviour`).
    """
    slug = artifact_common.normalise_slug(raw_slug)
    folder = product_dir / slug
    created = not folder.exists()
    folder.mkdir(parents=True, exist_ok=True)
    index_path = regenerate_product_index(product_dir)

    return {
        "slug": slug,
        "path": str(folder),
        "created": created,
        "index": str(index_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="docs/product/ artifact family query core")
    parser.add_argument("--exists", action="store_true")
    parser.add_argument("--resolve-slug", action="store_true")
    parser.add_argument("--check-freshness", action="store_true")
    parser.add_argument("--ensure-folder", action="store_true")
    # Required by --exists/--resolve-slug/--ensure-folder, optional for
    # --check-freshness (see below); left unrequired here so argparse's own
    # usage-text exit never fires and every failure this script reports is
    # JSON.
    parser.add_argument("--slug")
    parser.add_argument("--product-dir", required=True)
    args = parser.parse_args()

    # Exactly one entry-point flag is the only failure mode this script
    # owns; zero or several is a caller error, reported as JSON rather than
    # argparse's usage text so every failure this script reports is JSON.
    entry_points = {
        "exists": args.exists,
        "resolve_slug": args.resolve_slug,
        "check_freshness": args.check_freshness,
        "ensure_folder": args.ensure_folder,
    }
    chosen = [name for name, on in entry_points.items() if on]
    if len(chosen) != 1:
        print(
            json.dumps(
                {
                    "error": (
                        "exactly one of --exists, --resolve-slug, --check-freshness, "
                        f"--ensure-folder is required, got {len(chosen)} "
                        f"({', '.join(chosen) or 'none'})"
                    )
                },
                indent=2,
            )
        )
        return 1

    # --slug is required for --exists/--resolve-slug/--ensure-folder;
    # --check-freshness alone accepts it being absent (see
    # cmd_check_freshness).
    if chosen[0] in ("exists", "resolve_slug", "ensure_folder") and args.slug is None:
        print(
            json.dumps(
                {"error": f"--slug is required for --{chosen[0].replace('_', '-')}"},
                indent=2,
            )
        )
        return 1

    product_dir = Path(args.product_dir).expanduser().resolve()

    if args.exists:
        result = cmd_exists(args.slug, product_dir)
    elif args.resolve_slug:
        result = cmd_resolve_slug(args.slug, product_dir)
    elif args.ensure_folder:
        result = cmd_ensure_folder(args.slug, product_dir)
    else:
        result = cmd_check_freshness(args.slug, product_dir)

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
