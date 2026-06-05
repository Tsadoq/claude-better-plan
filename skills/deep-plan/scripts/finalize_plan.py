#!/usr/bin/env python3
"""Checkpoint 2 auto-repair normalizer and Phase 5 archiver for /deep-plan.

Two modes:

1. Repair (run before the Checkpoint 2 approval gate):
       finalize_plan.py --repair --plan <plan_path>
   Reads the plan file, repairs it in place, and prints a JSON report
   `{ok, fixes, warnings}`. Repair never loops: it normalizes em-dashes,
   task headers, missing sections, and missing task subsections rather
   than rejecting. `ok` is false only for genuinely unrecoverable input
   (empty file, or no tasks at all).

2. Archive (run after Checkpoint 2 approval):
       finalize_plan.py --archive --plan <plans-dir>/<slug>.md \
         --plans-dir <dir> --slug <slug>
   Repairs, then splits the appendix sections (`## Verification probes`,
   `## Research dossiers`) into sibling files and rewrites the lean plan
   at <plans-dir>/<slug>.md. Source and destination are the same file;
   the plan text is fully read before any write, so the in-place split
   is safe. Prints a JSON report with the written paths.

The single canonical plan file is plans_dir/<slug>.md (born as a
-draft.md in Phase 2, renamed at Phase 4.1); there is no mirror copy.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REQUIRED_SECTIONS = [
    "## Context",
    "## Decisions made",
    "## Architecture",
    "## Tasks",
    "## References",
    "## Open questions",
]

# Sections whose emptiness is worth a warning (Architecture and Open
# questions legitimately carry an `n/a` body, so they are excluded).
WARN_IF_EMPTY = {"## Context", "## Decisions made", "## Tasks", "## References"}

# Always-present task subsections. `**Tests (TDD)**` is intentionally NOT
# here: it is required only for tasks that touch code (see CODE_EXTS).
ALWAYS_TASK_SUBSECTIONS = [
    ("**Target files**", "n/a"),
    ("**Change**", "n/a"),
    ("**Verification**", "n/a"),
    ("**Depends on**", "none"),
]

CODE_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".rb",
    ".c", ".h", ".hpp", ".cc", ".cpp", ".cs", ".kt", ".swift", ".php",
    ".scala", ".sh", ".bash", ".zsh", ".sql", ".lua", ".pl", ".r", ".m",
}
DOC_EXTS = {
    ".md", ".markdown", ".rst", ".txt", ".yml", ".yaml", ".json", ".toml",
    ".ini", ".cfg", ".conf", ".env", ".csv", ".html", ".xml",
}

APPENDIX_PROBES = re.compile(r"^## Verification probes\b.*$", re.MULTILINE)
APPENDIX_RESEARCH = re.compile(r"^## Research(?: dossiers)?\b.*$", re.MULTILINE)

ATTRIBUTION = [
    re.compile(r"^Co-[Aa]uthored-[Bb]y: Claude\b.*$", re.MULTILINE),
    re.compile(r"^\U0001f916 Generated with.*$", re.MULTILINE),
    re.compile(r"^Generated with \[Claude Code\].*$", re.MULTILINE),
]


# --------------------------------------------------------------------------
# Section helpers
# --------------------------------------------------------------------------

def _header_pos(text: str, header: str) -> int:
    m = re.search(rf"^{re.escape(header)}[ \t]*$", text, re.MULTILINE)
    return m.start() if m else -1


def _section_end(text: str, start: int) -> int:
    m = re.search(r"^## ", text[start + 1 :], re.MULTILINE)
    return (start + 1 + m.start()) if m else len(text)


def _section_body(text: str, header: str) -> str:
    pos = _header_pos(text, header)
    if pos == -1:
        return ""
    end = _section_end(text, pos)
    # drop the header line itself
    nl = text.find("\n", pos)
    body = text[(nl + 1 if nl != -1 else end) : end]
    return body.strip()


# --------------------------------------------------------------------------
# Repair steps
# --------------------------------------------------------------------------

def strip_attribution(text: str, fixes: list[str]) -> str:
    for pat in ATTRIBUTION:
        new = pat.sub("", text)
        if new != text:
            fixes.append("removed AI attribution boilerplate")
            text = new
    return text


def normalize_task_headers(text: str, fixes: list[str]) -> str:
    pat = re.compile(r"^#{2,4}[ \t]+Task[ \t]+(\d+)\b[ \t]*[:.)\-–—]*[ \t]*(.*)$", re.MULTILINE)

    def repl(m: re.Match[str]) -> str:
        n, title = m.group(1), m.group(2).strip()
        out = f"### Task {n}: {title}".rstrip()
        if out != m.group(0):
            fixes.append(f"normalized header for task {n}")
        return out

    return pat.sub(repl, text)


def renumber_tasks(text: str, fixes: list[str], warnings: list[str]) -> str:
    headers = re.findall(r"^### Task (\d+):", text, re.MULTILINE)
    nums = [int(h) for h in headers]
    if nums and nums != list(range(1, len(nums) + 1)):
        counter = {"i": 0}

        def repl(m: re.Match[str]) -> str:
            counter["i"] += 1
            return f"### Task {counter['i']}:"

        text = re.sub(r"^### Task \d+:", repl, text, flags=re.MULTILINE)
        fixes.append(f"renumbered tasks to dense sequence (was {nums})")
        warnings.append("tasks were renumbered; double-check **Depends on** references")
    return text


def normalize_dashes(text: str, fixes: list[str]) -> str:
    new = re.sub(r"[ \t]*[—–][ \t]*", " -- ", text)
    if new != text:
        fixes.append("replaced em/en-dash with ` -- `")
    return new


def ensure_sections(text: str, fixes: list[str], warnings: list[str]) -> str:
    for i, sec in enumerate(REQUIRED_SECTIONS):
        if _header_pos(text, sec) != -1:
            if sec in WARN_IF_EMPTY and not _section_body(text, sec):
                warnings.append(f"section {sec} is empty")
            continue
        block = f"\n{sec}\n\nn/a\n"
        insert_pos: int | None = None
        for prev in reversed(REQUIRED_SECTIONS[:i]):
            p = _header_pos(text, prev)
            if p != -1:
                insert_pos = _section_end(text, p)
                break
        if insert_pos is None:
            for nxt in REQUIRED_SECTIONS[i + 1 :]:
                p = _header_pos(text, nxt)
                if p != -1:
                    insert_pos = p
                    block = f"{sec}\n\nn/a\n\n"
                    break
        if insert_pos is None:
            insert_pos = len(text)
        text = text[:insert_pos].rstrip() + "\n\n" + block.strip() + "\n\n" + text[insert_pos:].lstrip()
        fixes.append(f"inserted missing section {sec} with n/a body")
    return text


def _target_files(block: str) -> list[str]:
    m = re.search(r"\*\*Target files\*\*:\s*\n((?:[ \t]*-[ \t]*.+\n?)+)", block)
    if not m:
        return []
    files: list[str] = []
    for line in m.group(1).splitlines():
        line = line.strip().lstrip("-").strip()
        if line:
            files.append(line.split()[0])
    return files


def _is_code_task(block: str) -> bool:
    for f in _target_files(block):
        ext = Path(f.split("(")[0].strip()).suffix.lower()
        if ext in CODE_EXTS:
            return True
    return False


def ensure_task_subsections(text: str, fixes: list[str], warnings: list[str]) -> str:
    tasks_pos = _header_pos(text, "## Tasks")
    if tasks_pos == -1:
        return text
    tasks_end = _section_end(text, tasks_pos)
    head, body, tail = text[:tasks_pos], text[tasks_pos:tasks_end], text[tasks_end:]

    parts = re.split(r"(^### Task \d+:.*$)", body, flags=re.MULTILINE)
    # parts = [preamble, header1, block1, header2, block2, ...]
    rebuilt = [parts[0]]
    for k in range(1, len(parts), 2):
        header = parts[k]
        block = parts[k + 1] if k + 1 < len(parts) else ""
        n = re.search(r"Task (\d+):", header).group(1)  # type: ignore[union-attr]
        additions: list[str] = []
        for label, default in ALWAYS_TASK_SUBSECTIONS:
            if label not in block:
                additions.append(f"{label}: {default}")
                fixes.append(f"task {n}: inserted {label} with {default}")
                warnings.append(f"task {n}: {label} was missing, set to {default}")
        if "**Tests (TDD)**" not in block and _is_code_task(block):
            warnings.append(f"task {n} touches code but has no **Tests (TDD)** subsection")
        if additions:
            block = block.rstrip() + "\n\n" + "\n\n".join(additions) + "\n\n"
        rebuilt.append(header + "\n" if not header.endswith("\n") else header)
        rebuilt.append(block)
    new_body = "".join(rebuilt)
    return head + new_body + tail


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def repair(text: str) -> tuple[str, dict[str, Any]]:
    """Repair a plan body. Returns (repaired_text, report)."""
    fixes: list[str] = []
    warnings: list[str] = []

    if not text.strip():
        return text, {"ok": False, "fixes": [], "warnings": ["plan file is empty"]}

    text = strip_attribution(text, fixes)
    text = normalize_task_headers(text, fixes)
    text = renumber_tasks(text, fixes, warnings)
    text = normalize_dashes(text, fixes)
    text = ensure_sections(text, fixes, warnings)
    text = ensure_task_subsections(text, fixes, warnings)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"

    has_tasks = bool(re.search(r"^### Task \d+:", text, re.MULTILINE))
    if not has_tasks:
        warnings.append("no `### Task N:` entries found")
    ok = has_tasks
    return text, {"ok": ok, "fixes": fixes, "warnings": warnings}


def split_appendices(text: str) -> tuple[str, str | None, str | None]:
    """Pull appendix sections out of the plan. Returns (lean, probes, research)."""

    def _extract(pat: re.Pattern[str], body: str) -> tuple[str, str | None]:
        m = pat.search(body)
        if not m:
            return body, None
        start = m.start()
        end = _section_end(body, start)
        extracted = body[start:end].strip()
        lean = (body[:start].rstrip() + "\n\n" + body[end:].lstrip()).strip() + "\n"
        return lean, extracted

    lean, probes = _extract(APPENDIX_PROBES, text)
    lean, research = _extract(APPENDIX_RESEARCH, lean)
    return lean, probes, research


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def cmd_repair(plan: Path) -> dict[str, Any]:
    if not plan.exists():
        return {"ok": False, "fixes": [], "warnings": [f"plan file not found: {plan}"]}
    repaired, report = repair(plan.read_text())
    plan.write_text(repaired)
    report["plan"] = str(plan)
    return report


def cmd_archive(plan: Path, plans_dir: Path, slug: str) -> dict[str, Any]:
    if not plan.exists():
        return {"ok": False, "warnings": [f"plan file not found: {plan}"]}
    repaired, report = repair(plan.read_text())
    lean, probes, research = split_appendices(repaired)
    plans_dir.mkdir(parents=True, exist_ok=True)

    archive_path = plans_dir / f"{slug}.md"
    archive_path.write_text(lean)
    written = {"archive_path": str(archive_path)}

    if probes:
        probes_path = plans_dir / f"{slug}.probes.md"
        probes_path.write_text(probes.rstrip() + "\n")
        written["probes_path"] = str(probes_path)
    if research:
        research_path = plans_dir / f"{slug}.research.md"
        research_path.write_text(research.rstrip() + "\n")
        written["research_path"] = str(research_path)

    return {"ok": report["ok"], "fixes": report["fixes"], "warnings": report["warnings"], **written}


def main() -> int:
    parser = argparse.ArgumentParser(description="deep-plan plan repairer and archiver")
    parser.add_argument("--repair", action="store_true", help="normalize the plan in place")
    parser.add_argument(
        "--archive", action="store_true", help="split appendix siblings, rewrite lean plan"
    )
    parser.add_argument("--plan", required=True, help="path to the plan file")
    parser.add_argument("--plans-dir", help="archive destination dir (archive mode)")
    parser.add_argument("--slug", help="archive base name (archive mode)")
    args = parser.parse_args()

    plan = Path(args.plan).resolve()

    if args.archive:
        if not args.plans_dir or not args.slug:
            print(json.dumps({"ok": False, "warnings": ["--archive needs --plans-dir and --slug"]}))
            return 2
        result = cmd_archive(plan, Path(args.plans_dir).expanduser().resolve(), args.slug)
    else:
        result = cmd_repair(plan)

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok", False) else 1


if __name__ == "__main__":
    sys.exit(main())
