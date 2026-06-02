#!/usr/bin/env python3
"""Parse a finalized /deep-plan plan file into structured JSON.

Used by the `/deep-plan:deep-plan-execute` companion skill to turn a plan's
`## Tasks` block into a deterministic task list that can be loaded into the
harness Task API (one `TaskCreate` per task, then `TaskUpdate addBlockedBy`
to wire `Depends on`).

Usage:
    load_tasks.py --plan <path>

Output (stdout, JSON):
    {
      "tasks": [
        {"n": 1, "subject": "...", "target_files": ["src/x.py (new)"],
         "change": "...", "tests": "..."|null, "verification": "...",
         "depends_on": [int, ...]},
        ...
      ],
      "decisions": [{"n": "1", "decision": "...", "chosen": "...",
                     "rejected": "...", "rationale": "..."}, ...],
      "open_questions": "none"
    }

The shape mirrors the `## Tasks` subschema in
`references/plan-file-template.md`. Section slicing reuses the helpers in
`finalize_plan.py` rather than re-implementing them.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from finalize_plan import _header_pos, _section_body, _section_end

# A task subsection label line, e.g. `**Change**:` or `**Depends on**: none`.
_LABEL_RE = re.compile(r"^\*\*(?P<label>[^*]+)\*\*:[ \t]*(?P<inline>.*)$", re.MULTILINE)
_TASK_HEADER_RE = re.compile(r"^### Task (\d+):[ \t]*(.*)$", re.MULTILINE)


def parse_depends_on(value: str) -> list[int]:
    """Extract task numbers from a `Depends on` value.

    `none` / empty / malformed degrade to `[]` without raising; numeric tokens
    (single or comma-separated) become an ordered, de-duplicated int list.
    """
    seen: set[int] = set()
    ordered: list[int] = []
    for token in re.findall(r"\d+", value or ""):
        n = int(token)
        if n not in seen:
            seen.add(n)
            ordered.append(n)
    return ordered


def _split_subsections(block: str) -> dict[str, str]:
    """Map each `**Label**` in a task block to its body text."""
    matches = list(_LABEL_RE.finditer(block))
    out: dict[str, str] = {}
    for i, m in enumerate(matches):
        label = m.group("label").strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(block)
        inline = m.group("inline").strip()
        rest = block[body_start:body_end].strip()
        out[label] = (inline + ("\n" + rest if rest else "")).strip() if inline else rest
    return out


def _target_file_lines(body: str) -> list[str]:
    files: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("-"):
            entry = stripped.lstrip("-").strip()
            if entry:
                files.append(entry)
    return files


def _parse_tasks(text: str) -> list[dict[str, Any]]:
    tasks_pos = _header_pos(text, "## Tasks")
    if tasks_pos == -1:
        return []
    body = text[tasks_pos : _section_end(text, tasks_pos)]

    parts = re.split(r"(^### Task \d+:.*$)", body, flags=re.MULTILINE)
    # parts = [preamble, header1, block1, header2, block2, ...]
    tasks: list[dict[str, Any]] = []
    for k in range(1, len(parts), 2):
        header = parts[k]
        block = parts[k + 1] if k + 1 < len(parts) else ""
        hm = _TASK_HEADER_RE.match(header.strip())
        if not hm:
            continue
        subs = _split_subsections(block)
        tasks.append(
            {
                "n": int(hm.group(1)),
                "subject": hm.group(2).strip(),
                "target_files": _target_file_lines(subs.get("Target files", "")),
                "change": subs.get("Change", "").strip(),
                "tests": subs.get("Tests (TDD)", "").strip() or None,
                "verification": subs.get("Verification", "").strip(),
                "depends_on": parse_depends_on(subs.get("Depends on", "")),
            }
        )
    return tasks


def _parse_decisions(text: str) -> list[dict[str, str]]:
    body = _section_body(text, "## Decisions made")
    rows: list[dict[str, str]] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        # Skip header (`# | Decision | ...`) and separator (`---|---`) rows.
        if not cells or cells[0] in ("#", "") or set("".join(cells)) <= set("-: "):
            continue
        if not cells[0].isdigit():
            continue
        padded = (cells + [""] * 5)[:5]
        rows.append(
            {
                "n": padded[0],
                "decision": padded[1],
                "chosen": padded[2],
                "rejected": padded[3],
                "rationale": padded[4],
            }
        )
    return rows


def parse_plan(text: str) -> dict[str, Any]:
    """Parse a plan body into tasks, decisions, and the open-questions text."""
    return {
        "tasks": _parse_tasks(text),
        "decisions": _parse_decisions(text),
        "open_questions": _section_body(text, "## Open questions"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="parse a deep-plan plan file into structured JSON")
    parser.add_argument("--plan", required=True, help="path to the finalized plan file")
    args = parser.parse_args()

    plan = Path(args.plan).expanduser().resolve()
    if not plan.exists():
        print(json.dumps({"ok": False, "error": f"plan file not found: {plan}"}))
        return 1

    parsed = parse_plan(plan.read_text())
    parsed["ok"] = bool(parsed["tasks"])
    parsed["plan"] = str(plan)
    print(json.dumps(parsed, indent=2, sort_keys=True))
    return 0 if parsed["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
