#!/usr/bin/env python3
"""Phase 5 validator and mirror for /deep-plan.

Usage:
    finalize_plan.py --custom <custom_plan_path> --harness <harness_plan_path>

Validates that the custom plan file has every required section in the
right order. On success, copies the canonical to the harness mirror so
ExitPlanMode reads the right content.

Returns a JSON blob with `ok` and a list of validation errors.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

REQUIRED_SECTIONS_IN_ORDER = [
    "## Context",
    "## Decisions made",
    "## Architecture",
    "## Tasks",
    "## References",
    "## Open questions",
]

REQUIRED_TASK_SUBSECTIONS = [
    "**Target files**",
    "**Change**",
    "**Tests (TDD)**",
    "**Verification**",
    "**Depends on**",
]

def validate_section_order(text: str) -> list[str]:
    errors: list[str] = []
    last_index = -1
    for section in REQUIRED_SECTIONS_IN_ORDER:
        idx = text.find(f"\n{section}")
        if idx == -1 and not text.startswith(section):
            errors.append(f"missing required section: {section}")
            continue
        if idx <= last_index and not text.startswith(section):
            errors.append(
                f"section {section!r} is out of order (expected after previous required section)"
            )
        last_index = idx
    return errors


def validate_tasks(text: str) -> list[str]:
    errors: list[str] = []
    tasks_match = re.search(r"\n## Tasks\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    if not tasks_match:
        return ["Tasks section is empty or missing"]
    tasks_body = tasks_match.group(1)
    task_headers = re.findall(r"^### Task (\d+):", tasks_body, re.MULTILINE)
    if not task_headers:
        return ["Tasks section contains no `### Task N:` headers"]
    expected = list(range(1, len(task_headers) + 1))
    actual = [int(n) for n in task_headers]
    if actual != expected:
        errors.append(
            f"task numbering must be dense starting at 1; got {actual}, expected {expected}"
        )
    task_blocks = re.split(r"^### Task \d+: ", tasks_body, flags=re.MULTILINE)[1:]
    for n, block in enumerate(task_blocks, start=1):
        for sub in REQUIRED_TASK_SUBSECTIONS:
            if sub not in block:
                errors.append(f"task {n} missing subsection {sub}")
    return errors


def validate_em_dashes(text: str) -> list[str]:
    if "—" in text:
        return ["plan contains em-dash character; use ` -- ` or rephrase"]
    return []


def validate_no_ai_attribution(text: str) -> list[str]:
    patterns = [
        re.compile(r"^Co-[Aa]uthored-[Bb]y: Claude\b", re.MULTILINE),
        re.compile(r"^\xf0\x9f\xa4\x96 Generated with", re.MULTILINE),
        re.compile(r"^\U0001f916 Generated with", re.MULTILINE),
        re.compile(r"^Generated with \[Claude Code\]", re.MULTILINE),
    ]
    return [
        f"plan contains forbidden attribution boilerplate matching {p.pattern!r}"
        for p in patterns
        if p.search(text)
    ]


def validate(text: str) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_section_order(text))
    errors.extend(validate_tasks(text))
    errors.extend(validate_em_dashes(text))
    errors.extend(validate_no_ai_attribution(text))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="deep-plan plan validator and mirror")
    parser.add_argument("--custom", required=True)
    parser.add_argument("--harness", required=True)
    args = parser.parse_args()

    custom = Path(args.custom).resolve()
    harness = Path(args.harness).resolve()

    result: dict[str, Any] = {
        "ok": False,
        "validation_errors": [],
        "harness_path_written": False,
        "custom": str(custom),
        "harness": str(harness),
    }

    if not custom.exists():
        result["validation_errors"] = [f"custom plan file not found: {custom}"]
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    text = custom.read_text()
    errors = validate(text)
    result["validation_errors"] = errors

    if errors:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    harness.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(custom, harness)
    result["harness_path_written"] = True

    result["ok"] = True
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
