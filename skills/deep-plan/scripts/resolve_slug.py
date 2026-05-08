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
import re
import sys
from pathlib import Path
from typing import Any

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_SLUG_LEN = 60


def normalise_slug(raw: str) -> str:
    s = raw.strip().lower()
    s = re.sub(r"[^a-z0-9-]+", "-", s)
    s = re.sub(r"-+", "-", s)
    s = s.strip("-")
    if len(s) > MAX_SLUG_LEN:
        s = s[:MAX_SLUG_LEN].rstrip("-")
    return s


def is_valid_slug(s: str) -> bool:
    if not s or len(s) > MAX_SLUG_LEN:
        return False
    return bool(SLUG_RE.match(s))


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


def next_v_suffix(plans_dir: Path, slug: str) -> str:
    candidate = slug
    n = 2
    while (plans_dir / f"{candidate}.md").exists():
        candidate = f"{slug}-v{n}"
        n += 1
        if n > 999:
            return f"{slug}-v{n}"
    return candidate


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
        "path": str(plans_dir / f"{normalised}.md") if valid else None,
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

    target = plans_dir / f"{normalised}.md"
    if target.exists():
        result["collision"] = True
        result["collision_context"] = extract_context(target)
        result["auto_v_suffix"] = next_v_suffix(plans_dir, normalised)

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
