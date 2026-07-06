"""Tests for resolve_slug.py: normalisation, validation, and collision handling.

Runnable two ways:
    python3 skills/deep-plan/tests/test_resolve_slug.py
    python3 -m pytest skills/deep-plan/tests/test_resolve_slug.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

# resolve_slug imports finalize_plan as a sibling; put scripts/ on the path so
# both resolve when the test runner's cwd is elsewhere.
sys.path.insert(0, str(SCRIPTS))


def _load(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


resolve = _load("resolve_slug")


def _run_main(argv: list[str]) -> dict[str, Any]:
    old_argv = sys.argv
    sys.argv = ["resolve_slug", *argv]
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            resolve.main()
    finally:
        sys.argv = old_argv
    return json.loads(buf.getvalue())


def test_normalise_slug_lowercases_spaces_and_collapses_hyphens() -> None:
    assert resolve.normalise_slug("My Cool Slug") == "my-cool-slug"
    assert resolve.normalise_slug("a--b") == "a-b"
    assert resolve.normalise_slug("-leading-and-trailing-") == "leading-and-trailing"
    assert resolve.normalise_slug("Foo_Bar!Baz") == "foo-bar-baz"


def test_normalise_slug_caps_length() -> None:
    out = resolve.normalise_slug("x" * 70)
    assert len(out) <= resolve.MAX_SLUG_LEN
    # A truncation that lands on a hyphen is trimmed.
    assert not out.endswith("-")


def test_is_valid_slug() -> None:
    assert resolve.is_valid_slug("rate-limiter-redis")
    assert not resolve.is_valid_slug("")
    assert not resolve.is_valid_slug("x" * (resolve.MAX_SLUG_LEN + 1))
    assert not resolve.is_valid_slug("-bad")
    assert not resolve.is_valid_slug("Bad")
    assert not resolve.is_valid_slug("a--b")


def test_next_v_suffix_increments_on_collision() -> None:
    with tempfile.TemporaryDirectory() as d:
        plans = Path(d)
        (plans / "slug.md").write_text("x")
        (plans / "slug-v2.md").write_text("x")
        assert resolve.next_v_suffix(plans, "slug") == "slug-v3"


def test_collision_detected_with_context_and_auto_suffix() -> None:
    with tempfile.TemporaryDirectory() as d:
        plans = Path(d)
        (plans / "rate-limiter.md").write_text(
            "# Rate limiter\n\n## Context\n\nAdds a token-bucket limiter to the API.\n\n## Tasks\n"
        )
        result = _run_main(["--slug", "rate-limiter", "--plans-dir", str(plans)])
        assert result["collision"] is True
        assert "token-bucket" in result["collision_context"]
        assert result["auto_v_suffix"] == "rate-limiter-v2"


def test_folder_collision_and_v_suffix_skips_both_forms() -> None:
    # A folder plan alone is a collision, with context read from its plan.md.
    with tempfile.TemporaryDirectory() as d:
        plans = Path(d)
        (plans / "x").mkdir()
        (plans / "x" / "plan.md").write_text(
            "# X\n\n## Context\n\nFolder-form plan body.\n\n## Tasks\n"
        )
        result = _run_main(["--slug", "x", "--plans-dir", str(plans)])
        assert result["collision"] is True
        assert "Folder-form plan body" in result["collision_context"]

    # v-suffix search skips candidates existing in either form.
    with tempfile.TemporaryDirectory() as d:
        plans = Path(d)
        (plans / "x.md").write_text("x")
        (plans / "x-v2").mkdir()
        assert resolve.next_v_suffix(plans, "x") == "x-v3"

    # A collision-free slug resolves to the folder-write path.
    with tempfile.TemporaryDirectory() as d:
        result = _run_main(["--slug", "fresh", "--plans-dir", d])
        assert result["collision"] is False
        assert result["path"].endswith("/fresh/plan.md")


def test_no_collision_for_fresh_slug() -> None:
    with tempfile.TemporaryDirectory() as d:
        result = _run_main(["--slug", "brand-new-plan", "--plans-dir", d])
        assert result["collision"] is False
        assert result["valid"] is True
        assert result["collision_context"] is None


if __name__ == "__main__":
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
