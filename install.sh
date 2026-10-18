#!/usr/bin/env bash
# Installs the deep-plan skills into any agent that loads SKILL.md folders
# (Codex, pi, Claude Code, ...). Asks for the skills folder unless one is given.
#
#   ./install.sh [--force] [skills-dir]
#   ./install.sh --uninstall [skills-dir]
#   curl -fsSL https://raw.githubusercontent.com/tsadoq/claude-better-plan/main/install.sh | bash
#
# The full plugin (skills, agents, lib, PLAN.md) goes to $DEEP_PLAN_HOME
# (default: ${XDG_DATA_HOME:-~/.local/share}/deep-plan) with every
# ${CLAUDE_PLUGIN_ROOT} rewritten to that path, since only Claude Code sets the
# variable. Each skill folder is then copied into the skills folder you name.

set -euo pipefail

REPO_URL="https://github.com/tsadoq/claude-better-plan.git"
DEFAULT_SKILLS_DIR="$HOME/.agents/skills"
MARKER=".deep-plan-install"
PAYLOAD="${DEEP_PLAN_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/deep-plan}"

die() { echo "install.sh: $*" >&2; exit 1; }

force=0
uninstall=0
skills_dir=""
while [ $# -gt 0 ]; do
  case "$1" in
    --force) force=1 ;;
    --uninstall) uninstall=1 ;;
    -h|--help) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) die "unknown option: $1" ;;
    *) skills_dir="$1" ;;
  esac
  shift
done

if [ -z "$skills_dir" ]; then
  [ -r /dev/tty ] || die "no skills folder given and no terminal to ask on"
  echo "Folder your agent loads skills from:" >/dev/tty
  echo "  Codex / pi: ~/.agents/skills   Claude Code: ~/.claude/skills" >/dev/tty
  printf "Skills folder [%s]: " "$DEFAULT_SKILLS_DIR" >/dev/tty
  read -r skills_dir </dev/tty || true
  skills_dir="${skills_dir:-$DEFAULT_SKILLS_DIR}"
fi
case "$skills_dir" in "~"|"~/"*) skills_dir="$HOME${skills_dir#\~}" ;; esac

if [ "$uninstall" = 1 ]; then
  for dir in "$skills_dir"/*/; do
    [ -f "$dir$MARKER" ] && rm -rf "$dir" && echo "removed $dir"
  done
  [ -f "$PAYLOAD/$MARKER" ] && rm -rf "$PAYLOAD" && echo "removed $PAYLOAD"
  exit 0
fi

command -v python3 >/dev/null || die "python3 is required (the skills run stdlib-only Python helpers)"

# Install from the checkout this script sits in, or clone one when piped from curl.
src=""
script_path="${BASH_SOURCE[0]:-}"
if [ -n "$script_path" ] && [ -f "$script_path" ]; then
  src="$(cd "$(dirname "$script_path")" && pwd)"
fi
if [ -z "$src" ] || [ ! -f "$src/skills/deep-plan/SKILL.md" ]; then
  command -v git >/dev/null || die "git is required to fetch $REPO_URL"
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  git clone --quiet --depth 1 "$REPO_URL" "$tmp/repo"
  src="$tmp/repo"
fi

# Refuse to clobber folders this script did not create.
if [ -e "$PAYLOAD" ] && [ ! -f "$PAYLOAD/$MARKER" ] && [ "$force" = 0 ]; then
  die "$PAYLOAD exists and was not made by install.sh (use --force or set DEEP_PLAN_HOME)"
fi
skills=()
for skill_md in "$src"/skills/*/SKILL.md; do
  name="$(basename "$(dirname "$skill_md")")"
  dest="$skills_dir/$name"
  if [ -e "$dest" ] && [ ! -f "$dest/$MARKER" ] && [ "$force" = 0 ]; then
    die "$dest exists and was not made by install.sh (use --force to replace it)"
  fi
  skills+=("$name")
done

rm -rf "$PAYLOAD"
mkdir -p "$PAYLOAD"
tar -C "$src" --exclude='__pycache__' --exclude='tests' -cf - skills agents lib PLAN.md \
  | tar -C "$PAYLOAD" -xf -
touch "$PAYLOAD/$MARKER"

python3 - "$PAYLOAD" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
for path in root.rglob("*.md"):
    text = path.read_text(encoding="utf-8")
    if "${CLAUDE_PLUGIN_ROOT}" in text:
        path.write_text(text.replace("${CLAUDE_PLUGIN_ROOT}", str(root)), encoding="utf-8")
PY

mkdir -p "$skills_dir"
for name in "${skills[@]}"; do
  rm -rf "${skills_dir:?}/$name"
  cp -R "$PAYLOAD/skills/$name" "$skills_dir/$name"
  touch "$skills_dir/$name/$MARKER"
done

echo "Installed ${#skills[@]} skills into $skills_dir"
echo "Plugin files (scripts, agents, references) live in $PAYLOAD"
