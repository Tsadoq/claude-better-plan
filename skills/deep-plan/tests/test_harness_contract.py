"""Contract test: root-owned pytest discovery and the reproducible CI runner.

Pins pyproject.toml's [tool.pytest.ini_options] and ci.yml's runner shape so
test discovery is owned in exactly one place and no caller ever lists
per-skill test paths again. Stdlib only, so CI does not need pyyaml.

Runnable two ways:
    python3 skills/deep-plan/tests/test_harness_contract.py
    python3 -m pytest skills/deep-plan/tests/test_harness_contract.py
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PYPROJECT = ROOT / "pyproject.toml"
CI_YML = ROOT / ".github" / "workflows" / "ci.yml"


def _colocated_test_dirs() -> list[str]:
    """The repo layout is the source of truth for what discovery must cover."""
    return sorted(
        str(p.relative_to(ROOT)) for p in (ROOT / "skills").glob("*/tests") if p.is_dir()
    )


def test_pytest_config_discovers_colocated_skill_tests() -> None:
    expected = _colocated_test_dirs()
    config = tomllib.loads(PYPROJECT.read_text())
    ini = config.get("tool", {}).get("pytest", {}).get("ini_options", {})
    assert ini, "pyproject.toml missing the [tool.pytest.ini_options] table"
    assert sorted(ini.get("testpaths", [])) == expected, (
        f"tool.pytest.ini_options.testpaths must cover every co-located skill "
        f"test dir {expected}, got {ini.get('testpaths')}"
    )
    assert "--import-mode=importlib" in ini.get("addopts", ""), (
        "tool.pytest.ini_options.addopts must carry --import-mode=importlib"
    )

    ci = CI_YML.read_text()
    pytest_run_lines = [
        line for line in ci.splitlines() if "run:" in line and "pytest" in line
    ]
    assert pytest_run_lines, "ci.yml must run pytest"
    for line in pytest_run_lines:
        assert "skills/" not in line, (
            f"ci.yml pytest line must not carry a per-skill path: {line.strip()!r}"
        )
    assert "pytest>=9,<10" in ci, 'ci.yml install line must pin "pytest>=9,<10"'
    assert "tiktoken" in ci, (
        "ci.yml install line must list tiktoken (the token-budget contract test needs it)"
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
