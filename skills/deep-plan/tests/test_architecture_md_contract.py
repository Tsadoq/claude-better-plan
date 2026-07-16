"""Guards the architecture.md reference template's required shape.

architecture.md is the conditional plan-folder member for architecturally
significant plans. The template owns both the shape (Today / After this plan)
and the write-or-skip rubric Phase 4.4 quotes, so this test pins both.

Runnable two ways:
    python3 skills/deep-plan/tests/test_architecture_md_contract.py
    python3 -m pytest skills/deep-plan/tests/test_architecture_md_contract.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # skills/deep-plan
SCRIPTS = ROOT / "scripts"
TEMPLATE = ROOT / "references" / "architecture-md-template.md"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


finalize = _load("finalize_plan")


def test_architecture_template_required_sections() -> None:
    assert TEMPLATE.exists(), f"missing template: {TEMPLATE}"
    text = TEMPLATE.read_text()

    today = text.find("## Today")
    after = text.find("## After this plan")
    assert today != -1, "'## Today' section missing from architecture-md-template.md"
    assert after != -1, "'## After this plan' section missing from architecture-md-template.md"
    assert today < after, "'## Today' must precede '## After this plan'"

    assert "```mermaid" in text, (
        "the skeleton must carry a container/component-level mermaid fence"
    )
    assert "reversible" in text, (
        "the significance test must carry its skip-list "
        "(e.g. 'reversible within a sprint')"
    )
    assert "design.md" in text, (
        "the seam rule must name design.md as where decision rationale stays"
    )
    assert finalize.ARCHITECTURE_FILE_NAME == "architecture.md", (
        "finalize_plan.py must carry the architecture.md layout constant"
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
