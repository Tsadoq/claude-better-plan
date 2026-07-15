"""Tests for finalize_plan.py auto-repair and archive behavior.

Runnable two ways:
    python3 skills/deep-plan/tests/test_finalize.py     # stdlib, no deps
    python3 -m pytest skills/deep-plan/tests/test_finalize.py
"""

from __future__ import annotations

import importlib.util
import re
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
LEGACY = Path(__file__).resolve().parent / "golden" / "legacy-plan.md"


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


def test_layout_constants_and_resolve_plan_path() -> None:
    assert finalize.PLAN_FILE_NAME == "plan.md"
    assert finalize.RESEARCH_FILE_NAME == "research.md"
    assert finalize.PROBES_FILE_NAME == "probes.md"
    assert finalize.DESIGN_FILE_NAME == "design.md"
    assert finalize.ARCHITECTURE_FILE_NAME == "architecture.md"
    assert finalize.DRAFT_SUFFIX == "-draft"
    assert finalize.OVERVIEW_BEGIN == "<!-- deep-plan-task-overview:begin generated: do not edit -->"
    assert finalize.OVERVIEW_END == "<!-- deep-plan-task-overview:end -->"
    assert finalize.INDEX_BEGIN == "<!-- deep-plan-index:begin generated: do not edit -->"
    assert finalize.INDEX_END == "<!-- deep-plan-index:end -->"
    assert finalize.STATUSES == ("draft", "approved", "executed", "legacy")

    with tempfile.TemporaryDirectory() as d:
        folder = Path(d)
        assert finalize.resolve_plan_path(folder) == folder / "plan.md"
        file_path = folder / "some-plan.md"
        file_path.write_text("# x\n")
        assert finalize.resolve_plan_path(file_path) == file_path


def test_legacy_golden_repairs_clean() -> None:
    # Companion to test_load_tasks.test_legacy_plan_parses_and_repairs_clean,
    # kept here so this file's suite (the one every repair change runs) proves
    # on its own that new warnings never fire on plans in the frozen v0.7 shape.
    _, report = finalize.repair(LEGACY.read_text())
    assert report["ok"] is True
    assert report["fixes"] == [], f"legacy plan must repair with zero fixes, got {report['fixes']}"
    assert report["warnings"] == [], (
        f"legacy plan must repair with zero warnings, got {report['warnings']}"
    )


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


TESTS_FIELDS_PLAN = """# P

## Context

ctx

## Decisions made

d

## Architecture

n/a

## Tasks

### Task 1: Edit code with a legacy Tests block

**Target files**:
- src/a.py (modify)

**Change**:
Edit code.

**Tests (TDD)**:
- File: tests/test_a.py (new)
- Test name: `test_a`
- Asserts: calling a() returns 1.
- This test MUST fail before implementation begins.

**Verification**:
```
pytest tests/test_a.py -x
```

**Depends on**: none

### Task 2: Edit code with a full Tests block

**Target files**:
- src/b.py (modify)

**Change**:
Edit more code.

**Tests (TDD)**:
- File: tests/test_b.py (new)
- Test name: `test_b`
- Behavior: b() clamps negative inputs to zero.
- Level: unit
- Real vs mocked: b() runs real; nothing is patched.
- Setup: local literals in the test.
- Seams: none introduced.
- Dedup: nothing lower covers this.
- Asserts: b(-1) returns 0.
- This test MUST fail before implementation begins.

**Verification**:
```
pytest tests/test_b.py -x
```

**Depends on**: none

### Task 3: Edit docs

**Target files**:
- docs/x.md (modify)

**Change**:
Edit docs.

**Verification**:
```
grep x docs/x.md
```

**Depends on**: none

## References

- src/a.py

## Open questions

- none
"""


def test_incomplete_tests_block_warns_per_missing_field() -> None:
    repaired, report = finalize.repair(TESTS_FIELDS_PLAN)
    warns = report["warnings"]
    # Task 1's legacy block carries File, Test name, and Asserts; every other
    # canonical field must warn. Derived from TESTS_FIELDS so the schema stays
    # single-sourced in finalize_plan.py.
    missing_fields = tuple(f for f in finalize.TESTS_FIELDS if f not in ("File", "Test name", "Asserts"))
    assert len(missing_fields) == 6, "legacy block should be missing the six new fields"
    for field in missing_fields:
        hits = [w for w in warns if "task 1" in w and field in w]
        assert len(hits) == 1, f"expected exactly one task-1 warning for missing field {field!r}, got {hits}"
    assert not any("task 2" in w for w in warns), f"full nine-field block must not warn, got {warns}"
    assert not any("task 3" in w for w in warns), f"docs task must not get field warnings, got {warns}"

    # Warn only, never insert: repair leaves the block untouched, so a second
    # pass is byte-identical and still reports the same missing fields.
    again, report2 = finalize.repair(repaired)
    assert again == repaired, "field warnings must not mutate the plan text"
    for field in missing_fields:
        assert any("task 1" in w and field in w for w in report2["warnings"]), (
            f"second pass lost the task-1 warning for {field!r}"
        )


def test_first_sentence_pep257_edge_cases() -> None:
    s = "Bumps the plugin to v0.5.0 and renames finalize_plan.py entry points. Second sentence."
    assert finalize.first_sentence(s) == (
        "Bumps the plugin to v0.5.0 and renames finalize_plan.py entry points."
    )
    # No terminator anywhere: fall back to the first line.
    assert finalize.first_sentence("no terminator here\nsecond line") == "no terminator here"
    # Pipes and internal newlines must render as one table-safe cell.
    piped = "matches the `a|b` alternation\nacross lines. Second."
    assert finalize.first_sentence(piped) == "matches the `a\\|b` alternation across lines."


def test_repair_upserts_task_overview() -> None:
    repaired, _ = finalize.repair(CODE_VS_DOC)
    assert repaired.count(finalize.OVERVIEW_BEGIN) == 1
    assert repaired.count(finalize.OVERVIEW_END) == 1
    region_start = repaired.index(finalize.OVERVIEW_BEGIN)
    region_end = repaired.index(finalize.OVERVIEW_END) + len(finalize.OVERVIEW_END)
    assert "## Task overview" in repaired[region_start:region_end]
    between = repaired[region_end : repaired.index("## Tasks")]
    assert between.strip() == "", "overview region must sit immediately before ## Tasks"

    # Stale hand-edited content inside the markers is replaced wholesale.
    stale = repaired.replace("## Task overview", "## Task overview\n\nSTALE HAND EDIT", 1)
    re_repaired, _ = finalize.repair(stale)
    assert "STALE HAND EDIT" not in re_repaired

    # A second repair pass is byte-identical, including for a sentence
    # containing a pipe.
    piped_plan = CODE_VS_DOC.replace(
        "Edit docs.", "Handles the `a|b` regex\nacross lines. Edit docs."
    )
    once, _ = finalize.repair(piped_plan)
    twice, _ = finalize.repair(once)
    assert once == twice
    assert "a\\|b" in once


LINKED_PLAN = """# Linked demo

## Context

ctx

## Decisions made

| # | Decision | Chosen | Rejected | Rationale |
|---|----------|--------|----------|-----------|
| 1 | A | B | C | because ([why b?](design.md#ANCHOR)) |

## Architecture

n/a

## Tasks

### Task 1: Add a thing

**Target files**:
- docs/thing.md (new)

**Change**:
Add a thing.

**Verification**:
```
grep -q thing docs/thing.md
```

**Depends on**: none

## References

- docs/thing.md

## Open questions

- none
"""

LINKED_DESIGN = (
    "# Design: linked demo\n\n"
    "## Background\n\nprose\n\n"
    "## When does a plan deserve an architecture.md?\n\nDecision stated first.\n\n"
    "## Implementation notes\n"
)


def test_readability_warnings_dangling_headers_and_index_links() -> None:
    # Dangling headers: an empty section warns once by name; a parent heading
    # whose body is its own subheadings does not.
    dangling = "## Empty section\n\n## Tasks\n\n### Task 1: x\n\nbody\n"
    warns = finalize.warn_dangling_headers(dangling)
    hits = [w for w in warns if "## Empty section" in w]
    assert len(hits) == 1, f"expected exactly one dangling warning for '## Empty section', got {warns}"
    assert not any("## Tasks" in w for w in warns), (
        f"parent '## Tasks' over its own '### Task 1:' must not count as dangling, got {warns}"
    )

    # Index links: a punctuated question heading (dot and question mark)
    # resolves via the slug rule; an unmatched anchor warns once by name.
    good_plan = LINKED_PLAN.replace("ANCHOR", "when-does-a-plan-deserve-an-architecturemd")
    assert finalize.warn_unresolved_decision_links(good_plan, LINKED_DESIGN) == [], (
        "a decisions-index link matching a slugified design.md heading must not warn"
    )
    bad_plan = LINKED_PLAN.replace("ANCHOR", "missing")
    bad = finalize.warn_unresolved_decision_links(bad_plan, LINKED_DESIGN)
    assert len(bad) == 1 and "design.md#missing" in bad[0], (
        f"expected exactly one warning naming design.md#missing, got {bad}"
    )

    # Sibling discovery: cmd_repair and cmd_archive both find design.md by
    # path convention, warn without mutating, and a second pass agrees.
    with tempfile.TemporaryDirectory() as d:
        plans_dir = Path(d)
        folder = plans_dir / "linked-demo"
        folder.mkdir()
        plan_path = folder / "plan.md"
        normalized, _ = finalize.repair(bad_plan)
        plan_path.write_text(normalized)
        (folder / "design.md").write_text(LINKED_DESIGN)

        rep = finalize.cmd_repair(plan_path)
        assert rep["fixes"] == [], f"readability checks must not add fixes, got {rep['fixes']}"
        assert plan_path.read_text() == normalized, (
            "readability warnings must never mutate the plan text"
        )
        assert len([w for w in rep["warnings"] if "design.md#missing" in w]) == 1, (
            f"cmd_repair must report the unresolved index link once, got {rep['warnings']}"
        )
        assert not any("Implementation notes" in w for w in rep["warnings"]), (
            "design.md's legitimately-empty ## Implementation notes must stay exempt"
        )

        rep2 = finalize.cmd_repair(plan_path)
        assert plan_path.read_text() == normalized and any(
            "design.md#missing" in w for w in rep2["warnings"]
        ), "a second repair pass must stay byte-identical and re-report the warning"

        # No sibling design.md: the link check turns off entirely.
        bare = plans_dir / "bare"
        bare.mkdir()
        (bare / "plan.md").write_text(normalized)
        rep3 = finalize.cmd_repair(bare / "plan.md")
        assert not any("design.md#" in w for w in rep3["warnings"]), (
            f"without a sibling design.md the link check must not run, got {rep3['warnings']}"
        )

        arch = finalize.cmd_archive(plan=plan_path, plans_dir=plans_dir, slug="linked-demo")
        assert arch["fixes"] == [], f"archive readability checks must not add fixes, got {arch['fixes']}"
        assert any("design.md#missing" in w for w in arch["warnings"]), (
            f"cmd_archive must share the sibling link check, got {arch['warnings']}"
        )


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


def test_archive_splits_in_place() -> None:
    # Phase 5 calls cmd_archive with --plan pointing AT plans_dir/<slug>/plan.md:
    # source equals destination. Pin that the in-place split stays safe
    # (the plan text is fully read before any write).
    with tempfile.TemporaryDirectory() as d:
        plans_dir = Path(d)
        slug = "demo-plan"
        folder = plans_dir / slug
        folder.mkdir()
        plan_path = folder / "plan.md"
        plan_path.write_text(
            MESSY
            + "\n## Verification probes\n\n[probe 1]: echo hi\nhi\n"
            + "\n## Research dossiers\n\n### redis\nverdict: good\n"
        )

        result = finalize.cmd_archive(plan=plan_path, plans_dir=plans_dir, slug=slug)

        assert result["ok"] is True
        assert result["archive_path"] == str(plan_path)
        lean = plan_path.read_text()
        assert "## Verification probes" not in lean
        assert "## Research dossiers" not in lean
        assert "## Context" in lean, "lean plan keeps the core sections"
        assert "probe 1" in (folder / "probes.md").read_text()
        assert "redis" in (folder / "research.md").read_text()


def test_archive_writes_folder_members() -> None:
    with tempfile.TemporaryDirectory() as d:
        plans_dir = Path(d)
        slug = "demo-plan"
        draft = plans_dir / "demo-plan-draft.md"
        draft.write_text(
            MESSY
            + "\n## Verification probes\n\n[probe 1]: echo hi\nhi\n"
            + "\n## Research dossiers\n\n### redis\nverdict: good\n"
        )

        result = finalize.cmd_archive(plan=draft, plans_dir=plans_dir, slug=slug)

        folder = plans_dir / slug
        assert result["ok"] is True
        assert result["archive_path"] == str(folder / "plan.md")
        assert result["probes_path"] == str(folder / "probes.md")
        assert result["research_path"] == str(folder / "research.md")
        lean = (folder / "plan.md").read_text()
        assert "## Verification probes" not in lean, "lean plan drops appendix headings"
        assert "## Research dossiers" not in lean
        assert "probe 1" in (folder / "probes.md").read_text()
        assert "redis" in (folder / "research.md").read_text()
        assert not (plans_dir / f"{slug}.probes.md").exists(), "no dotted sibling"

        assert "**Status**: approved" in lean
        date_line = re.search(r"^\*\*Date\*\*: \d{4}-\d{2}-\d{2}$", lean, re.MULTILINE)
        assert date_line, "Date stamp missing or malformed"

        # A second (in-place) archive run preserves the stamped lines.
        result2 = finalize.cmd_archive(
            plan=folder / "plan.md", plans_dir=plans_dir, slug=slug
        )
        assert result2["ok"] is True
        lean2 = (folder / "plan.md").read_text()
        assert lean2.count("**Status**: approved") == 1
        assert date_line.group(0) in lean2


def test_index_regeneration_is_deterministic() -> None:
    with tempfile.TemporaryDirectory() as d:
        plans_dir = Path(d)
        (plans_dir / "alpha").mkdir()
        (plans_dir / "alpha" / "plan.md").write_text(
            "# Alpha plan\n\n**Status**: approved\n**Date**: 2026-07-01\n\n## Context\n\nx\n"
        )
        (plans_dir / "beta").mkdir()
        (plans_dir / "beta" / "plan.md").write_text("# Beta plan\n\n## Context\n\nx\n")
        (plans_dir / "legacy-plan.md").write_text("# Old flat plan\n\n## Context\n\nx\n")
        # Dotted siblings and the README itself must never be listed.
        (plans_dir / "legacy-plan.probes.md").write_text("# probes\n")
        (plans_dir / "legacy-plan.research.md").write_text("# research\n")

        readme = finalize.regenerate_index(plans_dir)
        first = readme.read_text()

        # A hand-written line outside the markers survives regeneration,
        # and regeneration is byte-identical across consecutive runs.
        readme.write_text("Hand-written intro.\n\n" + first)
        finalize.regenerate_index(plans_dir)
        second = (plans_dir / "README.md").read_text()
        assert second == "Hand-written intro.\n\n" + first
        finalize.regenerate_index(plans_dir)
        assert (plans_dir / "README.md").read_text() == second

        region = first[first.index(finalize.INDEX_BEGIN) : first.index(finalize.INDEX_END)]
        row_lines = [ln for ln in region.splitlines() if ln.startswith("| [")]
        assert len(row_lines) == 3, f"expected 3 rows, got {row_lines}"
        assert "alpha" in row_lines[0] and "Alpha plan" in row_lines[0]
        assert "approved" in row_lines[0] and "2026-07-01" in row_lines[0]
        assert "beta" in row_lines[1] and "draft" in row_lines[1]
        assert "legacy-plan" in row_lines[2] and "legacy" in row_lines[2]
        assert "README" not in region, "the index must not list itself"


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
