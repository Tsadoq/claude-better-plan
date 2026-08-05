
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


finalize_plan = _load("finalize_plan", SCRIPTS)


def test_markers_reproduce_the_shipped_plans_literals():
    m = artifact_common.markers("deep-plan")
    assert m.begin == "<!-- deep-plan-index:begin generated: do not edit -->"
    assert m.end == "<!-- deep-plan-index:end -->"


def test_markers_derives_from_the_name_argument():
    m = artifact_common.markers("product-artifacts")
    assert m.begin == "<!-- product-artifacts-index:begin generated: do not edit -->"
    assert m.end == "<!-- product-artifacts-index:end -->"
