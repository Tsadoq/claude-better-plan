from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
from render_hosts import host_pointer  # noqa: E402

from hosts.profile import ROOT  # noqa: E402

MANIFESTS = (".claude-plugin/plugin.json", "plugin.json", "package.json")


def test_every_harness_manifest_carries_the_same_version() -> None:
    versions = {path: json.loads((REPO / path).read_text())["version"] for path in MANIFESTS}
    assert len(set(versions.values())) == 1, f"manifest versions drifted: {versions}"


def test_codex_marketplace_points_at_its_own_build() -> None:
    marketplace = json.loads((REPO / ".agents/plugins/marketplace.json").read_text())
    (entry,) = marketplace["plugins"]
    assert entry["source"] == {"source": "local", "path": "./dist/codex"}, (
        f"the Codex marketplace entry points at {entry['source']}, not the Codex build"
    )
    build = REPO / entry["source"]["path"]
    assert (build / "plugin.json").read_bytes() == (REPO / "plugin.json").read_bytes(), (
        "dist/codex/plugin.json differs from the root plugin.json; run python3 tools/render_hosts.py codex"
    )
    assert (build / "skills/deep-plan/SKILL.md").is_file(), "dist/codex/ ships no skills/deep-plan/SKILL.md"


# npm packages pi itself provides at runtime; the pi build may only peer-depend on them.
PI_HOST_PACKAGES = (
    "@earendil-works/pi-agent-core",
    "@earendil-works/pi-coding-agent",
    "@earendil-works/pi-tui",
    "@earendil-works/pi-ai",
    "typebox",
)


def _npm_package(entry: str) -> str:
    """The package a ``node_modules/<pkg>/...`` entry names, scoped (``@scope/name``) or not."""
    parts = entry.removeprefix("node_modules/").split("/")
    return "/".join(parts[:2]) if parts[0].startswith("@") else parts[0]


def test_pi_package_points_at_its_own_build() -> None:
    package = json.loads((REPO / "package.json").read_text())
    assert "pi-package" in package["keywords"]
    entries = [*package["pi"]["skills"], *package["pi"].get("extensions", [])]
    dependencies = package.get("dependencies", {})
    peers = package.get("peerDependencies", {})

    for entry in entries:
        if entry.startswith("node_modules/"):
            assert _npm_package(entry) in dependencies, f"pi entry {entry} names an undeclared dependency"
        else:
            assert entry.startswith("./dist/pi/"), f"pi entry {entry} points outside dist/pi/"
            assert list(REPO.glob(entry.removeprefix("./"))), f"pi entry {entry} matches no file"

    hosted = sorted(d for d in dependencies if d.startswith("@earendil-works/") or d == "typebox")
    assert not hosted, f"host packages must be peers, not dependencies: {hosted}"
    wrong_peers = {p: peers.get(p) for p in PI_HOST_PACKAGES if peers.get(p) != "*"}
    assert not wrong_peers, f"host packages must peer-depend at '*': {wrong_peers}"


# A module specifier: an import/export statement's ``from`` (statements may span lines),
# a side-effect ``import "x"``, a dynamic ``import("x")``, or a ``require("x")``.
# Relative and ``node:`` specifiers are filtered out by the test.
_TS_SPECIFIER = re.compile(
    r"""(?m)^\s*(?:import|export)\b[^;"']*?\bfrom\s*["']([^"'\n]+)["']"""
    r"""|^\s*import\s*["']([^"'\n]+)["']"""
    r"""|\b(?:import|require)\(\s*["']([^"'\n]+)["']"""
)


def test_pi_extensions_import_only_declared_packages() -> None:
    package = json.loads((REPO / "package.json").read_text())
    declared = {**package.get("dependencies", {}), **package.get("peerDependencies", {})}
    imports = [
        (source.relative_to(REPO), spec)
        for source in sorted((REPO / "hosts/pi/extensions").rglob("*.ts"))
        for groups in _TS_SPECIFIER.findall(source.read_text(encoding="utf-8"))
        for spec in groups
        if spec and not spec.startswith((".", "/", "node:"))
    ]
    assert imports, "no bare npm import found in hosts/pi/extensions/; the scan is broken"
    undeclared = [f"{path}: {spec}" for path, spec in imports if _npm_package(spec) not in declared]
    assert not undeclared, "vendored pi extensions import undeclared packages:\n" + "\n".join(undeclared)


def _install(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "DEEP_PLAN_HOME": str(tmp_path / "payload")}
    return subprocess.run(
        ["bash", str(REPO / "install.sh"), *args], env=env, capture_output=True, text=True, check=False
    )


def test_install_script_copies_every_skill(tmp_path: Path) -> None:
    skills_dir = tmp_path / "skills"
    result = _install(tmp_path, str(skills_dir))
    assert result.returncode == 0, result.stderr

    shipped = sorted(p.parent.name for p in (REPO / "skills").glob("*/SKILL.md"))
    assert sorted(p.name for p in skills_dir.iterdir()) == shipped

    payload = tmp_path / "payload"
    assert (payload / "lib/artifact_common.py").is_file()
    assert (payload / "skills/product-artifacts/scripts/product_artifact.py").is_file()
    assert not list(payload.rglob("tests"))

    rerun = _install(tmp_path, str(skills_dir))
    assert rerun.returncode == 0, rerun.stderr


def test_install_resolves_the_root_placeholder_to_the_payload(tmp_path: Path) -> None:
    skills_dir = tmp_path / "skills"
    payload = tmp_path / "payload"
    result = _install(tmp_path, str(skills_dir))
    assert result.returncode == 0, result.stderr

    for md in [*skills_dir.rglob("*.md"), *payload.rglob("*.md")]:
        assert ROOT not in md.read_text(), f"unresolved {ROOT} in {md}"
    skill_md = skills_dir / "deep-plan/SKILL.md"
    assert str(payload) in skill_md.read_text(), f"{skill_md} never names the payload path {payload}"

    # Only the generic build carries HOST.md and the pointer line; the Claude-native source has neither.
    assert (payload / "HOST.md").is_file(), f"{payload} lacks HOST.md, so the generic build was not installed"
    pointer = host_pointer("generic").replace(ROOT, str(payload))
    assert pointer in skill_md.read_text(), f"{skill_md} lacks the generic pointer line {pointer!r}"


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
