"""Source-level contracts of the vendored pi extensions.

No TypeScript runs here: pytest pins only what the source text can show (which
tools get registered, which licence notice each file keeps). Runtime behaviour is
the manual ``tools/smoke_pi.sh``.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from hosts.pi.tools import NPM_TOOLS, VENDORED_TOOLS  # noqa: E402

PI_HOST = REPO / "hosts" / "pi"
EXTENSIONS = PI_HOST / "extensions"
LICENSES = PI_HOST / "THIRD_PARTY_LICENSES.md"
SMOKE_SCRIPT = REPO / "tools" / "smoke_pi.sh"
# How far into a file a copyright line may sit and still count as its header.
NOTICE_HEADER_LINES = 10

REGISTER_TOOL = re.compile(r"\bregisterTool\(")
TOOL_NAME = re.compile(r"""\bname:\s*["']([^"']+)["']""")


def _extension_sources() -> list[Path]:
    sources = sorted(EXTENSIONS.rglob("*.ts"))
    assert sources, f"no .ts files under {EXTENSIONS}"
    return sources


def _registered_tool_names(source: str) -> set[str]:
    """The first ``name:`` value after each ``registerTool(`` call in ``source``."""
    names = set()
    for call in REGISTER_TOOL.finditer(source):
        name = TOOL_NAME.search(source, call.end())
        if name:
            names.add(name.group(1))
    return names


def test_vendored_extensions_register_only_the_planned_tools() -> None:
    registered: set[str] = set()
    for path in _extension_sources():
        registered |= _registered_tool_names(path.read_text(encoding="utf-8"))

    assert registered == set(VENDORED_TOOLS), (
        f"registered by vendored extensions: {sorted(registered)}; planned: {sorted(VENDORED_TOOLS)}"
    )
    assert not registered & set(NPM_TOOLS), (
        f"vendored tools {sorted(registered)} collide with npm tools {sorted(NPM_TOOLS)}"
    )


def test_every_vendored_file_keeps_its_upstream_notice() -> None:
    listed = LICENSES.read_text(encoding="utf-8") if LICENSES.exists() else ""
    missing = []
    for path in _extension_sources():
        header = path.read_text(encoding="utf-8").splitlines()[:NOTICE_HEADER_LINES]
        has_notice = any("Copyright" in line for line in header)
        if not has_notice and path.relative_to(PI_HOST).as_posix() not in listed:
            missing.append(path.relative_to(REPO).as_posix())

    assert not missing, f"no Copyright header and not listed in {LICENSES.name}: {missing}"


def test_smoke_script_fails_loudly_without_pi(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for tool in ("python3", "bash"):
        found = shutil.which(tool)
        assert found, f"{tool} is needed to run this test"
        (bin_dir / tool).symlink_to(found)

    result = subprocess.run(
        [str(bin_dir / "bash"), str(SMOKE_SCRIPT)],
        env={**os.environ, "PATH": str(bin_dir)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, f"smoke script passed with no pi on PATH: {result.stdout}"
    assert "pi not found" in result.stderr, result.stderr


def test_smoke_script_times_out_a_silent_model(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    # A pi that never answers, and an npm that installs nothing, so no network or model is touched.
    stubs = {"pi": "#!/bin/sh\nexec sleep 30\n", "npm": "#!/bin/sh\nexit 0\n"}
    for name, body in stubs.items():
        stub = bin_dir / name
        stub.write_text(body, encoding="utf-8")
        stub.chmod(0o755)

    result = subprocess.run(
        ["bash", str(SMOKE_SCRIPT)],
        env={
            **os.environ,
            "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
            "SMOKE_TIMEOUT": "1",
            "PI_CODING_AGENT_DIR": str(tmp_path / "no-agent-dir"),
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )

    assert result.returncode != 0, f"smoke script passed with a silent pi: {result.stdout}"
    assert "did not answer within 1s" in result.stderr, result.stderr
