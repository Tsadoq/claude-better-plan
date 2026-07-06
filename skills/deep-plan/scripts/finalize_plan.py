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
       finalize_plan.py --archive --plan <plans-dir>/<slug>/plan.md \
         --plans-dir <dir> --slug <slug>
   Repairs, stamps **Status**/**Date** under the H1 when absent, then
   splits the appendix sections (`## Verification probes`,
   `## Research dossiers`) into the folder members probes.md and
   research.md and rewrites the lean plan at <plans-dir>/<slug>/plan.md.
   Source and destination may be the same file; the plan text is fully
   read before any write, so the in-place split is safe. Prints a JSON
   report with the written paths.

Every plan lives in its own folder plans_dir/<slug>/ with fixed member
names (plan.md, research.md, probes.md, design.md). The draft is born as
plans_dir/<topic>-draft/plan.md in Phase 2 and the folder is renamed to
plans_dir/<slug>/ at Phase 4.2; there is no mirror copy.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

# Plan-folder layout: every plan lives in plans_dir/<slug>/ with these
# fixed member names. resolve_slug.py and load_tasks.py import them from
# here so the layout has a single source of truth.
PLAN_FILE_NAME = "plan.md"
RESEARCH_FILE_NAME = "research.md"
PROBES_FILE_NAME = "probes.md"
DESIGN_FILE_NAME = "design.md"
DRAFT_SUFFIX = "-draft"

# Normative marker literals for generated regions. Content between a
# begin/end pair is owned by this script and rewritten wholesale.
OVERVIEW_BEGIN = "<!-- deep-plan-task-overview:begin generated: do not edit -->"
OVERVIEW_END = "<!-- deep-plan-task-overview:end -->"
INDEX_BEGIN = "<!-- deep-plan-index:begin generated: do not edit -->"
INDEX_END = "<!-- deep-plan-index:end -->"

# The authoritative status vocabulary for the `**Status**:` line in
# plan.md and the plans_dir README index.
STATUSES = ("draft", "approved", "executed", "legacy")

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

# Canonical `**Tests (TDD)**` field labels, in normative order. Single source
# of the schema: the template skeleton, the golden fixture, and the
# perspective agent are pinned to this tuple by the contract tests. A code
# task whose Tests block lacks a `- {field}:` bullet gets one warning per
# missing field; repair never inserts field lines (warn only, like the
# missing-block check below).
TESTS_FIELDS = (
    "File", "Test name", "Behavior", "Level", "Real vs mocked",
    "Setup", "Seams", "Dedup", "Asserts",
)

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
# Path helpers
# --------------------------------------------------------------------------

def resolve_plan_path(path: Path) -> Path:
    """Resolve a plan folder to its plan.md member; pass files through."""
    if path.is_dir():
        return path / PLAN_FILE_NAME
    return path


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
        if _is_code_task(block):
            if "**Tests (TDD)**" not in block:
                warnings.append(f"task {n} touches code but has no **Tests (TDD)** subsection")
            else:
                tests_body = _task_subsections(block).get("Tests (TDD)", "")
                for field in TESTS_FIELDS:
                    if not re.search(rf"^[ \t]*-[ \t]*{re.escape(field)}:", tests_body, re.MULTILINE):
                        warnings.append(f"task {n}: **Tests (TDD)** block missing field {field}")
        if additions:
            block = block.rstrip() + "\n\n" + "\n\n".join(additions) + "\n\n"
        rebuilt.append(header + "\n" if not header.endswith("\n") else header)
        rebuilt.append(block)
    new_body = "".join(rebuilt)
    return head + new_body + tail


# --------------------------------------------------------------------------
# Task overview generation
# --------------------------------------------------------------------------

_TASK_LABEL_RE = re.compile(r"^\*\*(?P<label>[^*]+)\*\*:[ \t]*(?P<inline>.*)$", re.MULTILINE)


def first_sentence(text: str) -> str:
    """First sentence of a Change block, PEP 257/Javadoc terminator rule.

    The sentence ends at the first `.` followed by whitespace or end of
    text, so dots inside versions (`v0.5.0`) and file names
    (`finalize_plan.py`) do not terminate it. Falls back to the whole
    first line when no terminator exists. Newlines and whitespace runs
    collapse to single spaces and `|` is escaped so the result is always
    table-safe.
    """
    flat = re.sub(r"\s+", " ", text.strip())
    m = re.search(r"\.(?=\s|$)", flat)
    if m:
        out = flat[: m.end()]
    else:
        first_line = text.strip().splitlines()[0] if text.strip() else ""
        out = re.sub(r"\s+", " ", first_line).strip()
    return out.replace("|", "\\|")


def _task_subsections(block: str) -> dict[str, str]:
    """Map each `**Label**` in a task block to its body text."""
    matches = list(_TASK_LABEL_RE.finditer(block))
    out: dict[str, str] = {}
    for i, m in enumerate(matches):
        label = m.group("label").strip()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(block)
        inline = m.group("inline").strip()
        rest = block[m.end() : body_end].strip()
        out[label] = (inline + ("\n" + rest if rest else "")).strip() if inline else rest
    return out


def _overview_tasks(text: str) -> list[dict[str, Any]]:
    tasks_pos = _header_pos(text, "## Tasks")
    if tasks_pos == -1:
        return []
    body = text[tasks_pos : _section_end(text, tasks_pos)]
    parts = re.split(r"(^### Task \d+:.*$)", body, flags=re.MULTILINE)
    tasks: list[dict[str, Any]] = []
    for k in range(1, len(parts), 2):
        header = parts[k]
        block = parts[k + 1] if k + 1 < len(parts) else ""
        m = re.match(r"^### Task (\d+):[ \t]*(.*)$", header.strip())
        if not m:
            continue
        subs = _task_subsections(block)
        tasks.append(
            {
                "n": int(m.group(1)),
                "subject": m.group(2).strip(),
                "files": _target_files(block),
                "deps": re.findall(r"\d+", subs.get("Depends on", "")),
                "change": subs.get("Change", ""),
            }
        )
    return tasks


def render_task_overview(tasks: list[dict[str, Any]]) -> str:
    """Render the generated Task overview region, markers included."""
    lines = [
        OVERVIEW_BEGIN,
        "## Task overview",
        "",
        "| # | Task | Files | Deps | Summary |",
        "|---|------|-------|------|---------|",
    ]
    for t in tasks:
        files = ", ".join(t["files"]) if t["files"] else "n/a"
        deps = ", ".join(t["deps"]) if t["deps"] else "none"
        cells = [
            str(t["n"]),
            str(t["subject"]).replace("|", "\\|"),
            files.replace("|", "\\|"),
            deps,
            first_sentence(t["change"]),
        ]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append(OVERVIEW_END)
    return "\n".join(lines)


def upsert_task_overview(text: str, fixes: list[str]) -> str:
    """Regenerate the Task overview region between its markers.

    Runs after ensure_sections/ensure_task_subsections so `## Architecture`
    and `## Tasks` are guaranteed present. Replaces an in-place region
    wholesale; inserts it immediately before `## Tasks` when missing; a
    stray region outside the Architecture..Tasks span is deleted and
    reinserted at the anchor (self-healing).
    """
    tasks = _overview_tasks(text)
    tasks_pos = _header_pos(text, "## Tasks")
    if tasks_pos == -1 or not tasks:
        return text
    region = render_task_overview(tasks)
    begin = text.find(OVERVIEW_BEGIN)
    end = text.find(OVERVIEW_END)
    if begin != -1 and end != -1 and end > begin:
        end_close = end + len(OVERVIEW_END)
        arch_pos = _header_pos(text, "## Architecture")
        if arch_pos != -1 and arch_pos < begin and end_close <= tasks_pos:
            if text[begin:end_close] != region:
                text = text[:begin] + region + text[end_close:]
                fixes.append("regenerated Task overview table")
            return text
        text = text[:begin].rstrip() + "\n\n" + text[end_close:].lstrip()
        tasks_pos = _header_pos(text, "## Tasks")
        if tasks_pos == -1:
            return text + "\n" + region + "\n"
    text = text[:tasks_pos].rstrip() + "\n\n" + region + "\n\n" + text[tasks_pos:]
    fixes.append("inserted generated Task overview before ## Tasks")
    return text


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
    text = upsert_task_overview(text, fixes)
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


def stamp_status_date(text: str, status: str, date: str) -> str:
    """Insert **Status**/**Date** lines under the H1, only when absent.

    Existing values are preserved so a re-archive is deterministic.
    """
    m = re.search(r"^# .*$", text, re.MULTILINE)
    if not m:
        return text
    stamps: list[str] = []
    if not re.search(r"^\*\*Status\*\*:", text, re.MULTILINE):
        stamps.append(f"**Status**: {status}")
    if not re.search(r"^\*\*Date\*\*:", text, re.MULTILINE):
        stamps.append(f"**Date**: {date}")
    if not stamps:
        return text
    return text[: m.end()] + "\n\n" + "\n".join(stamps) + text[m.end() :]


def cmd_archive(plan: Path, plans_dir: Path, slug: str) -> dict[str, Any]:
    plan = resolve_plan_path(plan)
    if not plan.exists():
        return {"ok": False, "warnings": [f"plan file not found: {plan}"]}
    repaired, report = repair(plan.read_text())
    lean, probes, research = split_appendices(repaired)
    lean = stamp_status_date(lean, "approved", date.today().isoformat())

    folder = plans_dir / slug
    folder.mkdir(parents=True, exist_ok=True)

    archive_path = folder / PLAN_FILE_NAME
    archive_path.write_text(lean)
    written = {"archive_path": str(archive_path)}

    if probes:
        probes_path = folder / PROBES_FILE_NAME
        probes_path.write_text(probes.rstrip() + "\n")
        written["probes_path"] = str(probes_path)
    if research:
        research_path = folder / RESEARCH_FILE_NAME
        research_path.write_text(research.rstrip() + "\n")
        written["research_path"] = str(research_path)

    written["index_path"] = str(regenerate_index(plans_dir))

    return {"ok": report["ok"], "fixes": report["fixes"], "warnings": report["warnings"], **written}


def regenerate_index(plans_dir: Path) -> Path:
    """Regenerate the plans README index between its markers.

    Deterministic: every cell derives from file content (title, Status,
    Date), never mtime, and rows sort by slug, so a merge conflict in
    README.md is resolved by regenerating rather than hand-editing.
    """
    entries: list[tuple[str, str, str, str]] = []
    for member in plans_dir.glob(f"*/{PLAN_FILE_NAME}"):
        slug = member.parent.name
        entries.append((slug, f"{slug}/{PLAN_FILE_NAME}", member.read_text(), "draft"))
    for flat in plans_dir.glob("*.md"):
        if flat.name == "README.md" or flat.name.endswith((".probes.md", ".research.md")):
            continue
        entries.append((flat.stem, flat.name, flat.read_text(), "legacy"))

    rows: list[str] = []
    for slug, link, text, default_status in sorted(entries, key=lambda e: e[0]):
        m = re.search(r"^# (.+)$", text, re.MULTILINE)
        title = m.group(1).strip() if m else slug
        sm = re.search(r"^\*\*Status\*\*:[ \t]*(.+)$", text, re.MULTILINE)
        status = sm.group(1).strip() if sm else default_status
        dm = re.search(r"^\*\*Date\*\*:[ \t]*(.+)$", text, re.MULTILINE)
        stamped = dm.group(1).strip() if dm else ""
        rows.append(f"| [{slug}]({link}) | {title} | {status} | {stamped} |")

    region = "\n".join(
        [
            INDEX_BEGIN,
            "| Plan | Title | Status | Date |",
            "|------|-------|--------|------|",
            *rows,
            INDEX_END,
        ]
    )

    readme = plans_dir / "README.md"
    if readme.exists():
        text = readme.read_text()
        begin = text.find(INDEX_BEGIN)
        end = text.find(INDEX_END)
        if begin != -1 and end != -1 and end > begin:
            text = text[:begin] + region + text[end + len(INDEX_END) :]
        else:
            text = text.rstrip() + "\n\n" + region + "\n"
    else:
        text = "# Plans\n\n" + region + "\n"
    readme.write_text(text)
    return readme


def main() -> int:
    parser = argparse.ArgumentParser(description="deep-plan plan repairer and archiver")
    parser.add_argument("--repair", action="store_true", help="normalize the plan in place")
    parser.add_argument(
        "--archive", action="store_true", help="split appendix members, rewrite lean plan"
    )
    parser.add_argument(
        "--index", action="store_true", help="regenerate the plans_dir README index"
    )
    parser.add_argument("--plan", help="path to the plan file (repair/archive modes)")
    parser.add_argument("--plans-dir", help="plans directory (archive/index modes)")
    parser.add_argument("--slug", help="archive folder name (archive mode)")
    args = parser.parse_args()

    if args.index:
        if not args.plans_dir:
            print(json.dumps({"ok": False, "warnings": ["--index needs --plans-dir"]}))
            return 2
        index_path = regenerate_index(Path(args.plans_dir).expanduser().resolve())
        result: dict[str, Any] = {"ok": True, "index_path": str(index_path)}
    elif args.archive:
        if not args.plan or not args.plans_dir or not args.slug:
            print(
                json.dumps(
                    {"ok": False, "warnings": ["--archive needs --plan, --plans-dir and --slug"]}
                )
            )
            return 2
        result = cmd_archive(
            Path(args.plan).resolve(), Path(args.plans_dir).expanduser().resolve(), args.slug
        )
    else:
        if not args.plan:
            print(json.dumps({"ok": False, "warnings": ["--repair needs --plan"]}))
            return 2
        result = cmd_repair(Path(args.plan).resolve())

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok", False) else 1


if __name__ == "__main__":
    sys.exit(main())
