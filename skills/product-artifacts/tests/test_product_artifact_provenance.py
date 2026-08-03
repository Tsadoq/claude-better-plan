"""Component test for product_artifact.py's --provenance-line entry point.

Pins the one behaviour the flag adds: a beat asks for the provenance line it
should write into a member, and gets either a line the published
`PROVENANCE_RE` accepts or `None` when there is no upstream to record --
never an error. `blob_sha` correctness and the four staleness states are
owned by test_product_artifact_freshness.py and are not re-asserted here.

Runnable two ways:
    python3 skills/product-artifacts/tests/test_product_artifact_provenance.py
    python3 -m pytest skills/product-artifacts/tests/test_product_artifact_provenance.py
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


def test_provenance_line_is_emitted_when_an_upstream_resolves_and_null_when_it_does_not() -> None:
    first, second = product_artifact.MEMBERS[0], product_artifact.MEMBERS[1]

    with tempfile.TemporaryDirectory() as d:
        product_dir = Path(d)

        # A slug whose first member exists: the second member's upstream
        # resolves, so a line must come back.
        resolvable = "widget-export"
        folder = product_dir / resolvable
        folder.mkdir()
        first_bytes = b"brief content the sha is taken over"
        (folder / first).write_bytes(first_bytes)

        result, code = _run_main(
            ["--provenance-line", "--slug", resolvable, "--member", second, "--product-dir", str(product_dir)]
        )
        assert code == 0, f"a resolvable upstream must exit 0, got {code} with {result!r}"
        line = result["line"]
        assert line is not None, (
            f"--provenance-line must emit a line for {second!r} when its upstream "
            f"{first!r} exists; got null (result: {result!r})"
        )
        match = product_artifact.PROVENANCE_RE.search(line)
        assert match is not None, (
            f"the emitted line must be one PROVENANCE_RE accepts, so the emitter and "
            f"the validator cannot drift; PROVENANCE_RE rejected {line!r}"
        )
        assert match.group(1) == first, (
            f"the emitted line must name {second!r}'s chain predecessor {first!r} as "
            f"its upstream; it named {match.group(1)!r} (line: {line!r})"
        )
        expected_sha = product_artifact.blob_sha(first_bytes)
        assert match.group(2) == expected_sha, (
            f"the emitted sha must be blob_sha over the upstream's current bytes "
            f"({expected_sha}); the line carried {match.group(2)} (line: {line!r})"
        )

        # The chain head has no upstream to record: null line, still exit 0.
        result, code = _run_main(
            ["--provenance-line", "--slug", resolvable, "--member", first, "--product-dir", str(product_dir)]
        )
        assert code == 0, f"the chain head is a finding, not an error; got exit {code} with {result!r}"
        assert result["line"] is None, (
            f"the chain head {first!r} has no upstream, so no line can be emitted for "
            f"it; got {result['line']!r}"
        )

        # Upstream file absent: null line, still exit 0.
        headless = "no-brief-yet"
        (product_dir / headless).mkdir()

        result, code = _run_main(
            ["--provenance-line", "--slug", headless, "--member", second, "--product-dir", str(product_dir)]
        )
        assert code == 0, (
            f"a missing upstream file is a finding, not an error; got exit {code} with {result!r}"
        )
        assert result["line"] is None, (
            f"{second!r}'s upstream {first!r} does not exist in {headless!r}, so there "
            f"is no sha to record; got {result['line']!r}"
        )

        # Invalid slug, with a decoy first member sitting directly in
        # product_dir: an unguarded `product_dir / normalise_slug("!!!")`
        # collapses to product_dir itself, which would hash the decoy and
        # emit it as a real member's provenance.
        (product_dir / first).write_bytes(b"decoy that belongs to no slug folder")

        result, code = _run_main(
            ["--provenance-line", "--slug", "!!!", "--member", second, "--product-dir", str(product_dir)]
        )
        assert code == 0, f"an invalid slug is a finding, not an error; got exit {code} with {result!r}"
        assert result["line"] is None, (
            f"an invalid slug has no folder that can be safely constructed for it, so "
            f"no line may be emitted; got {result['line']!r} -- a sha over a file "
            f"outside any slug folder"
        )


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
