"""Guards the plan-file template and a golden plan against finalize drift.

If a future edit desyncs `plan-file-template.md` or the golden example from
`finalize_plan.py`, these tests fail. This is the regression guard for the
original bug (validator required a section the template never mentioned).

Runnable two ways:
    python3 skills/deep-plan/tests/test_template_contract.py
    python3 -m pytest skills/deep-plan/tests/test_template_contract.py
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # skills/deep-plan
SCRIPTS = ROOT / "scripts"
TEMPLATE = ROOT / "references" / "plan-file-template.md"
GOLDEN = Path(__file__).resolve().parent / "golden" / "example-plan.md"
PERSPECTIVE = Path(__file__).resolve().parents[3] / "agents" / "dp-plan-perspective.md"

REQUIRED = [
    "## Context",
    "## Decisions made",
    "## Architecture",
    "## Tasks",
    "## References",
    "## Open questions",
]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


finalize = _load("finalize_plan")


def _extract_skeleton(text: str) -> str:
    m = re.search(r"````markdown\n(.*?)\n````", text, re.DOTALL)
    assert m, "skeleton code fence not found in plan-file-template.md"
    return m.group(1)


def test_template_skeleton_normalizes_to_valid() -> None:
    skeleton = _extract_skeleton(TEMPLATE.read_text())
    repaired, report = finalize.repair(skeleton)
    for sec in REQUIRED:
        assert sec in repaired, f"required section {sec} missing after repair"
    assert "—" not in repaired and "–" not in repaired, "em/en-dash survived repair"
    for line in repaired.splitlines():
        if line.startswith("### Task"):
            assert re.match(r"^### Task \d+: ", line), f"non-colon task header: {line!r}"
    again, _ = finalize.repair(repaired)
    assert again == repaired, "repair must be idempotent"


def test_template_declares_overview_markers_and_summary_rule() -> None:
    text = TEMPLATE.read_text()
    skeleton = _extract_skeleton(text)

    # Markers come from finalize_plan constants (never re-hardcoded here) and
    # appear exactly once each, wrapping the Task overview heading between
    # Architecture and Tasks in the skeleton.
    assert text.count(finalize.OVERVIEW_BEGIN) == 1
    assert text.count(finalize.OVERVIEW_END) == 1
    arch = skeleton.index("## Architecture")
    begin = skeleton.index(finalize.OVERVIEW_BEGIN)
    heading = skeleton.index("## Task overview")
    end = skeleton.index(finalize.OVERVIEW_END)
    tasks = skeleton.index("## Tasks")
    assert arch < begin < heading < end < tasks, (
        "Task overview region must sit between ## Architecture and ## Tasks"
    )

    # Formatting rules name the opening summary-sentence rule and the
    # folder member set.
    assert "plain-English summary sentence" in text
    for member in ("plan.md", "research.md", "probes.md", "design.md"):
        assert member in text, f"folder member {member} not named in template"

    # The dotted-sibling naming is gone.
    assert "<slug>.probes.md" not in text
    assert "<slug>.research.md" not in text


def test_template_declares_decisions_index_and_change_shape() -> None:
    text = TEMPLATE.read_text()
    skeleton = _extract_skeleton(text)

    # The decisions table is an index: each row's Rationale cell points into
    # the sibling design.md by anchor link instead of carrying the full story.
    assert "design.md#" in skeleton, (
        "skeleton decisions row must carry a design.md# anchor-link placeholder"
    )

    # Formatting rules declare the structured Change shape, the conditional
    # architecture.md member, and the pointer to the readability rules' home.
    assert "structured sub-bullets" in text, (
        "formatting rules must state the summary-sentence-then-sub-bullets Change rule"
    )
    assert "architecture.md" in text, (
        "the template must name the conditional architecture.md folder member"
    )
    assert "readability-principles.md" in text, (
        "formatting rules must point at readability-principles.md authoring rules"
    )

    # Probe entries explain themselves in four parts around the machine-stable
    # [probe N] first line.
    assert "[probe 1]:" in skeleton, "probes appendix must keep the [probe N] grep anchor"
    for part in ("Why:", "If it had failed:"):
        assert part in skeleton, f"probes appendix skeleton missing the {part!r} line"

    # The dossier appendix opens with the coverage table and defers the dossier
    # shape to its normative home instead of restating the retired labels.
    assert "| # | Decision | Dossier | Not researched because |" in skeleton, (
        "dossier appendix must open with the research coverage table header"
    )
    assert "Canonical snippet" not in text, (
        "the retired dossier section list must not survive in the template"
    )

    # The perspective agent drafts Change blocks in the same shape.
    perspective = PERSPECTIVE.read_text()
    assert "structured sub-bullets" in perspective, (
        "dp-plan-perspective.md output format must mirror the "
        "summary-sentence-then-sub-bullets Change rule"
    )

    # The golden plan exercises the house style: an indexed decision row and a
    # sub-bulleted Task 1 Change block.
    golden = GOLDEN.read_text()
    decisions = golden[golden.index("## Decisions made") : golden.index("## Architecture")]
    assert re.search(r"\]\(design\.md#[a-z0-9-]+\)", decisions), (
        "golden decisions table must link at least one rationale into design.md"
    )
    task1 = golden[golden.index("### Task 1") : golden.index("**Tests (TDD)**")]
    change1 = task1[task1.index("**Change**") :]
    assert "\n- " in change1, (
        "golden Task 1 Change must continue in sub-bullets after its summary sentence"
    )


def test_golden_plan_has_no_fixes_or_warnings() -> None:
    repaired, report = finalize.repair(GOLDEN.read_text())
    assert report["ok"] is True
    assert report["fixes"] == [], f"golden plan should need no fixes, got {report['fixes']}"
    assert report["warnings"] == [], f"golden plan should have no warnings, got {report['warnings']}"


def _tests_block(text: str, source: str) -> str:
    start = text.find("**Tests (TDD)**")
    assert start != -1, f"{source}: no **Tests (TDD)** block found"
    end = text.find("**Verification**", start)
    assert end != -1, f"{source}: Tests block not followed by **Verification**"
    return text[start:end]


def test_template_and_golden_declare_full_tests_schema() -> None:
    skeleton = _extract_skeleton(TEMPLATE.read_text())
    golden = GOLDEN.read_text()
    for source, block in (
        ("template skeleton", _tests_block(skeleton, "template skeleton")),
        ("golden plan", _tests_block(golden, "golden plan")),
    ):
        # Labels come from finalize_plan.TESTS_FIELDS (never re-typed here);
        # bullet order must follow the tuple so the copies cannot silently
        # reorder relative to the canonical schema.
        positions: list[int] = []
        for label in finalize.TESTS_FIELDS:
            m = re.search(rf"^[ \t]*-[ \t]*{re.escape(label)}:", block, re.MULTILINE)
            assert m, f"{source}: Tests block missing a '- {label}:' bullet"
            positions.append(m.start())
        assert positions == sorted(positions), (
            f"{source}: Tests field bullets out of TESTS_FIELDS order"
        )


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
