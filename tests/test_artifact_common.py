"""Tests for lib/artifact_common.py's marker literal contract.

Runnable two ways:
    python3 -m pytest tests/test_artifact_common.py
    uvx pytest tests/test_artifact_common.py -q
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "lib"
SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "deep-plan" / "scripts"

sys.path.insert(0, str(LIB))
import artifact_common  # noqa: E402


def _load(name: str, directory: Path):
    spec = importlib.util.spec_from_file_location(name, directory / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Imported (not compared against) so this test exercises both modules the
# behaviour spans today, per the task's Real vs mocked note. Comparing this
# module's INDEX_BEGIN/INDEX_END against artifact_common.markers("deep-plan")
# is deliberately withheld: Task 2 makes those constants derive from
# markers("deep-plan"), which would turn the comparison into asserting a
# value against itself.
finalize_plan = _load("finalize_plan", SCRIPTS)


def test_markers_reproduce_the_shipped_plans_literals():
    m = artifact_common.markers("deep-plan")
    assert m.begin == "<!-- deep-plan-index:begin generated: do not edit -->"
    assert m.end == "<!-- deep-plan-index:end -->"


def test_markers_derives_from_the_name_argument():
    """Guards against a `markers()` that ignores `name` and returns a
    constant pair: a second family name must produce a different pair."""
    m = artifact_common.markers("product-artifacts")
    assert m.begin == "<!-- product-artifacts-index:begin generated: do not edit -->"
    assert m.end == "<!-- product-artifacts-index:end -->"
