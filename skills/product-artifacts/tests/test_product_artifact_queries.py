
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
ARTIFACT_FAMILY = Path(__file__).resolve().parent.parent / "references" / "artifact-family.md"


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


def _members_in_chain_order() -> list[str]:
    text = ARTIFACT_FAMILY.read_text()
    section = text.split("## Members", 1)[1].split("\n## ", 1)[0]
    return re.findall(r"^\|\s*`([a-z0-9-]+\.md)`\s*\|", section, re.MULTILINE)


def test_exists_reports_partial_chain_and_rejects_traversal_slug() -> None:
    members = _members_in_chain_order()
    assert members == list(product_artifact.MEMBERS)

    with tempfile.TemporaryDirectory() as d:
        product_dir = Path(d)
        folder = product_dir / "widget-export"
        folder.mkdir()
        (folder / members[0]).write_text("brief content")
        (folder / members[1]).write_text("discovery content")

        result, code = _run_main(
            ["--exists", "--slug", "widget-export", "--product-dir", str(product_dir)]
        )

        assert code == 0
        assert result["present"] is True
        assert list(result["members"].keys()) == members
        assert result["members"][members[0]] is True
        assert result["members"][members[1]] is True
        assert result["members"][members[2]] is False
        assert result["members"][members[3]] is False
        assert result["members"][members[4]] is False

    with tempfile.TemporaryDirectory() as d:
        product_dir = Path(d)
        result, code = _run_main(
            [
                "--resolve-slug",
                "--slug",
                "../../etc/passwd",
                "--product-dir",
                str(product_dir),
            ]
        )

        assert code == 0
        slug = result["slug"]
        assert "/" not in slug
        assert "." not in slug
        resolved_path = Path(result["path"]).resolve()
        assert resolved_path == product_dir.resolve() / slug
        assert str(resolved_path).startswith(str(product_dir.resolve()))


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
