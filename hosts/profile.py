"""How one host build rewrites the Claude-native source.

A host profile lives in ``hosts/<name>/__init__.py`` as ``PROFILE``. The renderer
(``tools/render_hosts.py``) reads it; nothing here touches the filesystem.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

# The placeholders every non-Claude build writes in place of Claude Code's
# substituted variables. Each host's HOST.md defines them for the model; this
# module is their only owner, so profiles and tests import them, never restate them.
ROOT = "<root>"
SESSION = "<session-id>"

Frontmatter = dict[str, str]
"""A markdown frontmatter as ``key -> value``, in source order.

A value is the raw YAML text after ``key:``: the rest of the key's line (leading
space removed) plus any indented continuation lines, so a block scalar reads
``"|\\n  line one"`` and a list reads ``"\\n  - item"``.
"""


@dataclass(frozen=True)
class HostProfile:
    """The rewrite rules for one host build.

    ``tokens`` are ``(regex, replacement)`` pairs applied in order with ``re.sub``
    to every markdown file, after overlays, so a replacement may use ``\\1``.

    ``drop_frontmatter`` names keys removed from every markdown frontmatter
    (comment lines directly above a dropped key go with it). ``agent_frontmatter``,
    when set, then maps each ``agents/*.md`` frontmatter to the host's.

    ``overlays_dir`` holds files named ``<relative md path>#<exact heading>.md``,
    for example ``skills/deep-plan/SKILL.md### R2: Approval enforcement.md``. Each
    replaces that heading's whole section, heading line included; an empty
    overlay deletes the section.

    ``extra_files`` maps a build-relative path to a repo-relative source file or
    directory, copied verbatim.

    ``extends`` names a parent profile: its tokens run before this profile's,
    its dropped keys and extra files add to this profile's, its
    ``agent_frontmatter`` applies when this profile sets none, and its overlays
    apply unless this profile overlays the same file and heading.
    """

    name: str
    tokens: tuple[tuple[str, str], ...] = ()
    drop_frontmatter: tuple[str, ...] = ()
    agent_frontmatter: Callable[[Frontmatter], Frontmatter] | None = None
    overlays_dir: Path | None = None
    extra_files: Mapping[str, str] = field(default_factory=dict)
    extends: HostProfile | None = None
