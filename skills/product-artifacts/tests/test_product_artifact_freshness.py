
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

EMPTY_BLOB_SHA = "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"


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


def _provenance_format_literal() -> str:
    text = ARTIFACT_FAMILY.read_text()
    section = text.split("## Provenance", 1)[1].split("\n## ", 1)[0]
    match = re.search(r"```\n(.+?)\n```", section, re.DOTALL)
    assert match, "artifact-family.md's ## Provenance section has no fenced format literal"
    return match.group(1).strip()


def _write_with_provenance(
    folder: Path, member: str, body: str, upstream: str, upstream_bytes: bytes
) -> None:
    sha = product_artifact.blob_sha(upstream_bytes)
    (folder / member).write_text(f"{body}\n\n**Derived from**: {upstream} ({sha})\n")


def test_freshness_separates_stale_from_unresolvable_and_exits_zero() -> None:
    assert product_artifact.blob_sha(b"") == EMPTY_BLOB_SHA

    literal = _provenance_format_literal()
    concrete_line = literal.replace("<upstream member>", "brief.md").replace("<git blob sha>", EMPTY_BLOB_SHA)
    assert product_artifact.PROVENANCE_RE.search(concrete_line) is not None

    first, second, third, fourth, fifth = product_artifact.MEMBERS

    with tempfile.TemporaryDirectory() as d:
        product_dir = Path(d)
        slug = "widget-export"
        folder = product_dir / slug
        folder.mkdir()

        original_first_bytes = b"brief v1 content"
        (folder / first).write_bytes(original_first_bytes)

        _write_with_provenance(folder, second, "discovery content", first, original_first_bytes)

        (folder / third).write_text(f"requirements content\n\n**Derived from**: {second} (deadbeef)\n")


        (folder / first).write_bytes(b"brief v2 content, rewritten after the fact")

        result, code = _run_main(["--check-freshness", "--slug", slug, "--product-dir", str(product_dir)])

        assert code == 0
        entries = result["entries"]
        assert len(entries) == 1
        members_state = entries[0]["members"]
        assert list(members_state.keys()) == list(product_artifact.MEMBERS)
        assert members_state[first] == "fresh"
        assert members_state[second] == "stale"
        assert members_state[third] == "unresolvable"
        assert members_state[fourth] == "absent"
        assert members_state[fifth] == "absent"

        result, code = _run_main(
            ["--check-freshness", "--slug", "no-such-slug", "--product-dir", str(product_dir)]
        )
        assert code == 0
        assert result["entries"][0]["members"] == dict.fromkeys(product_artifact.MEMBERS, "absent")


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
