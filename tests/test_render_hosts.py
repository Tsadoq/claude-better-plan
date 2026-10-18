from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
from render_hosts import RenderError, diff_build, host_pointer, main, render  # noqa: E402

from hosts.profile import ROOT, Frontmatter, HostProfile  # noqa: E402

HOST = "h"
SKILL = "skills/x/SKILL.md"


def _tree(tmp_path: Path) -> Path:
    """A one-skill source tree: SKILL.md with sections A and B, a script, a tests/ dir, a HOST.md."""
    src = tmp_path / "src"
    skill = src / "skills" / "x"
    (skill / "scripts").mkdir(parents=True)
    (skill / "tests").mkdir()
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: x\n"
        "allowed-tools: Read, Bash\n"
        "---\n"
        "\n"
        "# X\n"
        "\n"
        "## A\n"
        "\n"
        "Source text of A.\n"
        "\n"
        "## B\n"
        "\n"
        "Call ClaudeOnlyTool here.\n"
    )
    (skill / "scripts" / "a.py").write_bytes(b"print('a')\r\n\x00raw\n")
    (skill / "tests" / "t.py").write_text("def test_t(): pass\n")
    (src / "hosts" / HOST).mkdir(parents=True)
    (src / "hosts" / HOST / "HOST.md").write_text("# Host h\n")
    return src


def _overlay(overlays: Path, md_rel: str, heading: str, text: str) -> None:
    path = overlays / f"{md_rel}#{heading}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _section(md: str, heading: str) -> str:
    """The text from `heading` up to the next heading of the same level, heading line included."""
    start = md.index(heading + "\n")
    level = heading.split(" ")[0]
    rest = md[start + len(heading) + 1 :]
    end = rest.find("\n" + level + " ")
    return md[start:] if end == -1 else md[start : start + len(heading) + 1 + end + 1]


def test_overlay_replaces_its_section_and_tokens_rewrite_the_rest(tmp_path: Path) -> None:
    src = _tree(tmp_path)
    overlays = tmp_path / "overlays"
    _overlay(overlays, SKILL, "## A", "## A\n\nHost text of A.\n")
    profile = HostProfile(name=HOST, tokens=((r"ClaudeOnlyTool", "the host tool"),), overlays_dir=overlays)

    render(src, profile, tmp_path / "out")

    source_b = _section((src / SKILL).read_text(), "## B")
    assert "Call ClaudeOnlyTool here." in source_b, "fixture lost the token"
    md = (tmp_path / "out" / SKILL).read_text()
    assert _section(md, "## A") == "## A\n\nHost text of A.\n\n", "overlay for ## A not applied"
    assert "Call the host tool here." in _section(md, "## B"), "token ClaudeOnlyTool not rewritten in ## B"


def test_frontmatter_keys_are_dropped_and_the_host_pointer_follows_frontmatter(tmp_path: Path) -> None:
    src = _tree(tmp_path)
    profile = HostProfile(name=HOST, drop_frontmatter=("allowed-tools",))

    render(src, profile, tmp_path / "out")

    assert "allowed-tools: Read, Bash" in (src / SKILL).read_text(), "fixture lost the key to drop"
    md = (tmp_path / "out" / SKILL).read_text()
    _, frontmatter, body = md.split("---\n", 2)
    assert "allowed-tools" not in frontmatter, f"allowed-tools survived in frontmatter: {frontmatter!r}"
    first_body_line = next(line for line in body.splitlines() if line.strip())
    assert first_body_line == host_pointer(HOST), f"first body line is {first_body_line!r}, not the pointer"
    assert f"{ROOT}/HOST.md" in first_body_line, f"pointer does not name {ROOT}/HOST.md: {first_body_line!r}"


def test_non_markdown_is_copied_verbatim_and_tests_are_excluded(tmp_path: Path) -> None:
    src = _tree(tmp_path)
    out = tmp_path / "out"

    render(src, HostProfile(name=HOST), out)

    differing = diff_build(src / "skills" / "x" / "scripts", out / "skills" / "x" / "scripts")
    assert differing == [], f"scripts not copied byte-for-byte: {differing}"
    assert not (out / "skills" / "x" / "tests").exists(), "tests/ leaked into the build"


def test_child_profile_overlay_wins_over_parent_on_the_same_heading(tmp_path: Path) -> None:
    src = _tree(tmp_path)
    parent_overlays = tmp_path / "parent-overlays"
    child_overlays = tmp_path / "child-overlays"
    _overlay(parent_overlays, SKILL, "## A", "## A\n\nParent A.\n")
    _overlay(parent_overlays, SKILL, "## B", "## B\n\nParent B.\n")
    _overlay(child_overlays, SKILL, "## A", "## A\n\nChild A.\n")
    parent = HostProfile(name="base", overlays_dir=parent_overlays)
    child = HostProfile(name=HOST, overlays_dir=child_overlays, extends=parent)

    render(src, child, tmp_path / "out")

    md = (tmp_path / "out" / SKILL).read_text()
    assert "Child A." in _section(md, "## A"), "child overlay did not win on ## A"
    assert "Parent B." in _section(md, "## B"), "parent overlay for ## B not applied under extends"


def test_render_rejects_an_overlay_whose_heading_is_gone(tmp_path: Path) -> None:
    src = _tree(tmp_path)
    overlays = tmp_path / "overlays"
    _overlay(overlays, SKILL, "## Missing", "## Missing\n\nNowhere to go.\n")

    with pytest.raises(RenderError) as raised:
        render(src, HostProfile(name=HOST, overlays_dir=overlays), tmp_path / "out")

    assert "SKILL.md" in str(raised.value) and "## Missing" in str(raised.value), str(raised.value)


def test_render_rejects_an_overlay_for_a_file_not_in_the_build(tmp_path: Path) -> None:
    src = _tree(tmp_path)
    overlays = tmp_path / "overlays"
    _overlay(overlays, "skills/gone/SKILL.md", "## A", "## A\n\nOrphan.\n")

    with pytest.raises(RenderError) as raised:
        render(src, HostProfile(name=HOST, overlays_dir=overlays), tmp_path / "out")

    assert "skills/gone/SKILL.md" in str(raised.value), str(raised.value)


def test_render_rejects_an_overlay_whose_heading_occurs_twice(tmp_path: Path) -> None:
    src = _tree(tmp_path)
    (src / SKILL).write_text("# X\n\n## A\n\nOne.\n\n## A\n\nTwo.\n")
    overlays = tmp_path / "overlays"
    _overlay(overlays, SKILL, "## A", "## A\n\nNew.\n")

    with pytest.raises(RenderError) as raised:
        render(src, HostProfile(name=HOST, overlays_dir=overlays), tmp_path / "out")

    assert "## A" in str(raised.value) and "2 times" in str(raised.value), str(raised.value)


def test_headings_inside_code_fences_do_not_count_as_sections(tmp_path: Path) -> None:
    src = _tree(tmp_path)
    (src / SKILL).write_text("# X\n\n## A\n\n```\n## A\n## B\n```\n\n## B\n\nKept B.\n")
    overlays = tmp_path / "overlays"
    _overlay(overlays, SKILL, "## A", "## A\n\nNew A.\n")

    render(src, HostProfile(name=HOST, overlays_dir=overlays), tmp_path / "out")

    md = (tmp_path / "out" / SKILL).read_text()
    assert "```" not in md, f"fenced block inside ## A was not replaced with its section: {md!r}"
    assert _section(md, "## B") == "## B\n\nKept B.\n", f"## B after the fence was disturbed: {md!r}"


def test_diff_build_reports_one_sided_and_changed_files_and_ignores_excluded_dirs(tmp_path: Path) -> None:
    expected, actual = tmp_path / "expected", tmp_path / "actual"
    for tree in (expected, actual):
        (tree / "__pycache__").mkdir(parents=True)
        (tree / "same.txt").write_text("same\n")
    (expected / "changed.txt").write_bytes(b"old\n")
    (actual / "changed.txt").write_bytes(b"new\n")
    (expected / "only-expected.txt").write_text("e\n")
    (actual / "only-actual.txt").write_text("a\n")
    (actual / "__pycache__" / "m.pyc").write_bytes(b"\x00")

    differing = diff_build(expected, actual)

    assert differing == ["changed.txt", "only-actual.txt", "only-expected.txt"], differing


def test_extra_files_are_copied_verbatim_and_a_missing_one_stops_the_render(tmp_path: Path) -> None:
    src = _tree(tmp_path)
    (src / "extra" / "dir" / "tests").mkdir(parents=True)
    (src / "extra" / "one.json").write_bytes(b'{"a": 1}\r\n')
    (src / "extra" / "dir" / "two.txt").write_text("two\n")
    (src / "extra" / "dir" / "tests" / "t.py").write_text("def test_t(): pass\n")
    out = tmp_path / "out"
    profile = HostProfile(name=HOST, extra_files={"one.json": "extra/one.json", "d": "extra/dir"})

    render(src, profile, out)

    assert (out / "one.json").read_bytes() == b'{"a": 1}\r\n', "extra file not copied byte-for-byte"
    assert (out / "d" / "two.txt").read_text() == "two\n", "extra directory not copied"
    assert not (out / "d" / "tests").exists(), "tests/ inside an extra directory leaked into the build"
    with pytest.raises(RenderError) as raised:
        render(src, HostProfile(name=HOST, extra_files={"x": "extra/absent"}), out)
    assert "extra/absent" in str(raised.value), str(raised.value)


def _rename_tools(frontmatter: Frontmatter) -> Frontmatter:
    return {("host-tools" if k == "tools" else k): v for k, v in frontmatter.items()}


def test_agent_frontmatter_maps_agents_only_and_is_inherited_through_extends(tmp_path: Path) -> None:
    src = _tree(tmp_path)
    (src / "agents").mkdir()
    (src / "agents" / "a.md").write_text("---\nname: a\ntools: Read\n---\n\nAgent body.\n")
    parent = HostProfile(name="base", agent_frontmatter=_rename_tools)
    child = HostProfile(name=HOST, extends=parent)

    render(src, child, tmp_path / "out")

    agent = (tmp_path / "out" / "agents" / "a.md").read_text()
    assert agent == "---\nname: a\nhost-tools: Read\n---\n\nAgent body.\n", agent
    skill = (tmp_path / "out" / SKILL).read_text()
    assert "allowed-tools: Read, Bash" in skill, "agent mapping touched a skill"


def test_host_md_is_written_at_the_build_root_and_a_missing_one_stops_the_render(tmp_path: Path) -> None:
    src = _tree(tmp_path)
    (src / "hosts" / HOST / "HOST.md").write_text("# Host h\n\nDefines <root>.\n")
    out = tmp_path / "out"

    render(src, HostProfile(name=HOST), out)

    assert (out / "HOST.md").read_text() == "# Host h\n\nDefines <root>.\n", "HOST.md not copied to the root"
    with pytest.raises(RenderError) as raised:
        render(src, HostProfile(name="nohost"), out)
    assert "nohost" in str(raised.value), str(raised.value)


def _cli_repo(tmp_path: Path) -> Path:
    """A source tree whose hosts/h/ package defines PROFILE, as the CLI discovers profiles."""
    repo = _tree(tmp_path)
    (repo / "hosts" / HOST / "__init__.py").write_text(
        f"from hosts.profile import HostProfile\n\nPROFILE = HostProfile(name={HOST!r})\n"
    )
    return repo


def test_cli_writes_dist_and_check_passes_on_a_fresh_build(tmp_path: Path) -> None:
    repo = _cli_repo(tmp_path)

    assert main([HOST], repo=repo) == 0, "render exited non-zero"
    assert (repo / "dist" / HOST / SKILL).is_file(), "CLI did not write dist/<host>/"
    assert main(["--check"], repo=repo) == 0, "--check flagged a build it just wrote"


def test_cli_check_reports_a_stale_build_and_exits_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _cli_repo(tmp_path)
    main([HOST], repo=repo)
    (repo / "dist" / HOST / SKILL).write_text("hand edit\n")
    capsys.readouterr()

    status = main(["--check", HOST], repo=repo)

    captured = capsys.readouterr()
    assert status == 1, "--check passed a stale build"
    assert captured.out.splitlines() == [f"dist/{HOST}/{SKILL}"], captured.out
    assert f"python3 tools/render_hosts.py {HOST}" in captured.err, captured.err
    assert (repo / "dist" / HOST / SKILL).read_text() == "hand edit\n", "--check rewrote the committed build"


def test_cli_rejects_an_unknown_host(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = _cli_repo(tmp_path)

    with pytest.raises(SystemExit) as raised:
        main(["nosuch"], repo=repo)

    assert raised.value.code == 2, raised.value.code
    assert "nosuch" in capsys.readouterr().err
