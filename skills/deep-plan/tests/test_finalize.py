"""Tests for finalize_plan.py auto-repair and archive behavior.

Runnable two ways:
    python3 skills/deep-plan/tests/test_finalize.py     # stdlib, no deps
    python3 -m pytest skills/deep-plan/tests/test_finalize.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


finalize = _load("finalize_plan")


MESSY = """# Demo plan

## Context

This plan uses an em-dash — like this — in prose.

## Decisions made

| # | Decision | Chosen | Rejected | Rationale |
|---|----------|--------|----------|-----------|
| 1 | A | B | C | because |

## Tasks

### Task 1 — Add a thing

**Target files**:
- src/thing.py (new)

**Change**:
Add a thing.

**Verification**:
```
pytest -x
```

## References

- src/thing.py

## Open questions

- none
"""


def test_repair_fixes_emdash_headers_and_missing_sections() -> None:
    repaired, report = finalize.repair(MESSY)
    assert "—" not in repaired, "em-dash should be normalized away"
    assert "### Task 1: Add a thing" in repaired
    assert "### Task 1 —" not in repaired
    assert "## Architecture" in repaired
    idx_dec = repaired.index("## Decisions made")
    idx_arch = repaired.index("## Architecture")
    idx_tasks = repaired.index("## Tasks")
    assert idx_dec < idx_arch < idx_tasks, "Architecture must sit between Decisions and Tasks"
    for label in ("**Target files**", "**Change**", "**Verification**", "**Depends on**"):
        assert label in repaired, f"missing always-required subsection {label}"
    assert report["fixes"], "fixes should be recorded"
    assert report["ok"] is True


CODE_VS_DOC = """# P

## Context

ctx

## Decisions made

d

## Architecture

n/a

## Tasks

### Task 1: Edit docs

**Target files**:
- docs/x.md (modify)

**Change**:
Edit docs.

**Verification**:
```
grep x docs/x.md
```

**Depends on**: none

### Task 2: Edit code

**Target files**:
- src/y.py (modify)

**Change**:
Edit code.

**Verification**:
```
pytest -x
```

**Depends on**: none

## References

- docs/x.md

## Open questions

- none
"""


def test_doc_task_needs_no_tests_code_task_warns() -> None:
    _, report = finalize.repair(CODE_VS_DOC)
    warns = report["warnings"]
    assert any("task 2" in w and "Tests" in w for w in warns), "code task 2 should warn about missing tests"
    assert not any("task 1" in w and "Tests" in w for w in warns), "doc task 1 must not warn about tests"


def test_archive_extracts_siblings() -> None:
    plan = MESSY + (
        "\n## Verification probes\n\n[probe 1]: echo hi\nhi\n"
        "\n## Research dossiers\n\n### redis\nverdict: good\n"
    )
    lean, probes, research = finalize.split_appendices(plan)
    assert "## Verification probes" not in lean
    assert "## Research dossiers" not in lean
    assert "## Context" in lean, "lean plan keeps the core sections"
    assert probes and "probe 1" in probes
    assert research and "redis" in research


if __name__ == "__main__":
    import sys
    import traceback

    failed = 0
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"PASS {_name}")
            except Exception:  # noqa: BLE001
                failed += 1
                print(f"FAIL {_name}")
                traceback.print_exc()
    sys.exit(1 if failed else 0)
