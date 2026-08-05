
from __future__ import annotations

from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "references" / "design-md-template.md"


def test_design_template_required_sections() -> None:
    assert TEMPLATE.exists(), f"missing template: {TEMPLATE}"
    text = TEMPLATE.read_text()
    needles = [
        "# Design:",
        "## Background",
        "## {plain-language question",
        "first sentence",
        "## Implementation notes",
    ]
    pos = -1
    for needle in needles:
        found = text.find(needle, pos + 1)
        assert found > pos, f"{needle!r} missing or out of order in design-md-template.md"
        pos = found


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
