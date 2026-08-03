#!/usr/bin/env python3
"""Phase 4 slug normaliser and collision checker for /deep-plan.

Usage:
    resolve_slug.py --slug <slug> --plans-dir <dir>

Returns a JSON blob describing:
- the normalised slug (or a corrected suggestion if the input was invalid)
- whether the slug collides with an existing plan in plans_dir
- if collision: the existing file's `## Context` paragraph, so the
  orchestrator can decide between refine / overwrite / -v2 suffix
- the auto-incremented v-suffix that would resolve the collision
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Plugin-root lib/ carries the slug rules and marker convention shared with
# every artifact family; see lib/artifact_common.py's module docstring for
# why this is a sys.path bootstrap rather than a package import.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
import artifact_common  # noqa: E402
from finalize_plan import PLAN_FILE_NAME, resolve_plan_path  # noqa: E402

MAX_SLUG_LEN = artifact_common.MAX_SLUG_LEN
normalise_slug = artifact_common.normalise_slug
is_valid_slug = artifact_common.is_valid_slug

# The plans family's legacy collision form: a slug can be taken by a flat
# `<slug>.md` file as well as by a folder.
_LEGACY_SUFFIXES = (".md",)


def next_v_suffix(plans_dir: Path, slug: str) -> str:
    return artifact_common.next_v_suffix(plans_dir, slug, _LEGACY_SUFFIXES)


def extract_context(file_path: Path) -> str:
    try:
        text = file_path.read_text()
    except Exception:
        return ""
    in_context = False
    chunks: list[str] = []
    for line in text.splitlines():
        if line.strip().startswith("## Context"):
            in_context = True
            continue
        if in_context:
            if line.startswith("## "):
                break
            if line.strip() or chunks:
                chunks.append(line)
    return "\n".join(chunks).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="deep-plan slug normaliser")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--plans-dir", required=True)
    args = parser.parse_args()

    plans_dir = Path(args.plans_dir).expanduser().resolve()
    plans_dir.mkdir(parents=True, exist_ok=True)

    raw = args.slug
    normalised = normalise_slug(raw)
    valid = is_valid_slug(normalised)

    result: dict[str, Any] = {
        "input": raw,
        "slug": normalised,
        "valid": valid,
        "path": str(plans_dir / normalised / PLAN_FILE_NAME) if valid else None,
        "collision": False,
        "collision_context": None,
        "auto_v_suffix": None,
        "plans_dir": str(plans_dir),
    }

    if not valid:
        result["error"] = (
            f"slug {raw!r} is not valid after normalisation (got {normalised!r}). "
            f"Required: 1 to {MAX_SLUG_LEN} chars, [a-z0-9-], no leading/trailing/double hyphens."
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    folder = plans_dir / normalised
    flat = plans_dir / f"{normalised}.md"
    if artifact_common.slug_taken(plans_dir, normalised, _LEGACY_SUFFIXES):
        result["collision"] = True
        # Prefer the folder's plan.md; fall back to the legacy flat file.
        existing = resolve_plan_path(folder) if folder.exists() else flat
        result["collision_context"] = extract_context(existing)
        result["auto_v_suffix"] = next_v_suffix(plans_dir, normalised)

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
