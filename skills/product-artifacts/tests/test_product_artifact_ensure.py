"""Component test for product_artifact.py's --ensure-folder entry point.

Runnable two ways:
    python3 skills/product-artifacts/tests/test_product_artifact_ensure.py
    python3 -m pytest skills/product-artifacts/tests/test_product_artifact_ensure.py
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


def _load(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


product_artifact = _load("product_artifact")


def _run_main(argv: list[str]) -> tuple[dict[str, Any], int]:
    old_argv = sys.argv
    sys.argv = ["product_artifact", *argv]
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            code = product_artifact.main()
    finally:
        sys.argv = old_argv
    return json.loads(buf.getvalue()), code


def _generated_region(readme_text: str) -> str:
    """Text strictly between the product markers, exclusive of the markers
    themselves."""
    m = product_artifact.artifact_common.markers("product")
    begin = readme_text.find(m.begin)
    end = readme_text.find(m.end)
    assert begin != -1 and end != -1, "product markers missing from README"
    return readme_text[begin + len(m.begin) : end]


def _outer_halves(readme_text: str) -> tuple[str, str]:
    """(prefix before the begin marker, suffix after the end marker), so a
    disturbed prefix and a disturbed suffix are reported as two distinct
    failures rather than one combined diff."""
    m = product_artifact.artifact_common.markers("product")
    begin = readme_text.find(m.begin)
    end = readme_text.find(m.end)
    assert begin != -1 and end != -1, "product markers missing from README"
    return readme_text[:begin], readme_text[end + len(m.end) :]


def test_ensure_folder_is_idempotent_and_repairs_a_missing_index_row() -> None:
    slug = "widget-export"

    with tempfile.TemporaryDirectory() as d:
        product_dir = Path(d)
        readme = product_dir / "README.md"

        # First call: the folder does not exist yet, so this call creates
        # it and writes the index row for the first time.
        first, code = _run_main(
            ["--ensure-folder", "--slug", slug, "--product-dir", str(product_dir)]
        )
        assert code == 0
        assert first["created"] is True
        assert (product_dir / slug).is_dir()

        first_text = readme.read_text()
        first_prefix, first_suffix = _outer_halves(first_text)
        first_region = _generated_region(first_text)
        assert first_region.count(f"| {slug} ") == 1

        # Second call: same slug, folder already exists -- a true no-op on
        # the folder, but the index is still (re)written.
        second, code = _run_main(
            ["--ensure-folder", "--slug", slug, "--product-dir", str(product_dir)]
        )
        assert code == 0
        assert second["created"] is False

        second_text = readme.read_text()
        second_prefix, second_suffix = _outer_halves(second_text)
        assert second_prefix == first_prefix, "prefix before begin marker changed on a no-op call"
        assert second_suffix == first_suffix, "suffix after end marker changed on a no-op call"

        # Simulate the index row for this slug being lost or hand-edited:
        # delete it from the generated region while leaving the folder (and
        # everything outside the markers) untouched.
        m = product_artifact.artifact_common.markers("product")
        begin = second_text.find(m.begin)
        end = second_text.find(m.end)
        region = second_text[begin + len(m.begin) : end]
        stripped_region = "\n".join(
            line for line in region.splitlines() if f"| {slug} " not in line
        )
        damaged_text = second_text[: begin + len(m.begin)] + stripped_region + second_text[end:]
        readme.write_text(damaged_text)
        assert f"| {slug} " not in _generated_region(readme.read_text())

        # Third call: the folder still exists (no-op again), but the index
        # row must be restored.
        third, code = _run_main(
            ["--ensure-folder", "--slug", slug, "--product-dir", str(product_dir)]
        )
        assert code == 0
        assert third["created"] is False

        third_text = readme.read_text()
        third_prefix, third_suffix = _outer_halves(third_text)
        assert third_prefix == first_prefix, "prefix before begin marker was disturbed by repair"
        assert third_suffix == first_suffix, "suffix after end marker was disturbed by repair"

        repaired_region = _generated_region(third_text)
        assert repaired_region.count(f"| {slug} ") == 1


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
