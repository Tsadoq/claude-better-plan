from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFESTS = (".claude-plugin/plugin.json", "plugin.json", "package.json")


def test_every_harness_manifest_carries_the_same_version() -> None:
    versions = {path: json.loads((REPO / path).read_text())["version"] for path in MANIFESTS}
    assert len(set(versions.values())) == 1, f"manifest versions drifted: {versions}"


def test_codex_marketplace_points_at_the_repo_root() -> None:
    marketplace = json.loads((REPO / ".agents/plugins/marketplace.json").read_text())
    (entry,) = marketplace["plugins"]
    assert entry["name"] == json.loads((REPO / "plugin.json").read_text())["name"]
    assert entry["source"] == {"source": "local", "path": "./"}


def test_pi_package_declares_the_skills_folder() -> None:
    package = json.loads((REPO / "package.json").read_text())
    assert "pi-package" in package["keywords"]
    assert package["pi"]["skills"] == ["./skills"]


def _install(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "DEEP_PLAN_HOME": str(tmp_path / "payload")}
    return subprocess.run(
        ["bash", str(REPO / "install.sh"), *args], env=env, capture_output=True, text=True, check=False
    )


def test_install_script_copies_every_skill_with_resolved_paths(tmp_path: Path) -> None:
    skills_dir = tmp_path / "skills"
    result = _install(tmp_path, str(skills_dir))
    assert result.returncode == 0, result.stderr

    shipped = sorted(p.parent.name for p in (REPO / "skills").glob("*/SKILL.md"))
    assert sorted(p.name for p in skills_dir.iterdir()) == shipped

    payload = tmp_path / "payload"
    for md in [*skills_dir.rglob("*.md"), *payload.rglob("*.md")]:
        assert "${CLAUDE_PLUGIN_ROOT}" not in md.read_text(), f"unresolved plugin root in {md}"
    assert (payload / "lib/artifact_common.py").is_file()
    assert (payload / "skills/product-artifacts/scripts/product_artifact.py").is_file()
    assert not list(payload.rglob("tests"))

    rerun = _install(tmp_path, str(skills_dir))
    assert rerun.returncode == 0, rerun.stderr


def test_install_script_refuses_to_replace_a_foreign_skill(tmp_path: Path) -> None:
    skills_dir = tmp_path / "skills"
    (skills_dir / "deep-plan").mkdir(parents=True)
    (skills_dir / "deep-plan/SKILL.md").write_text("mine")

    result = _install(tmp_path, str(skills_dir))
    assert result.returncode != 0
    assert (skills_dir / "deep-plan/SKILL.md").read_text() == "mine"
    assert not (tmp_path / "payload").exists()


def test_uninstall_removes_only_what_install_made(tmp_path: Path) -> None:
    skills_dir = tmp_path / "skills"
    assert _install(tmp_path, str(skills_dir)).returncode == 0
    (skills_dir / "unrelated").mkdir()

    result = _install(tmp_path, "--uninstall", str(skills_dir))
    assert result.returncode == 0, result.stderr
    assert [p.name for p in skills_dir.iterdir()] == ["unrelated"]
    assert not (tmp_path / "payload").exists()
