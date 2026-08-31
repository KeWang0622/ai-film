#!/usr/bin/env bash
# Install the ai-film skill for Claude Code.
#
#   ./install.sh              -> ~/.claude/skills/ai-film
#   ./install.sh --project    -> ./.claude/skills/ai-film  (this repo only)
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/skills/ai-film"
DEST="${HOME}/.claude/skills"
[[ "${1:-}" == "--project" ]] && DEST="$(pwd)/.claude/skills"

if [[ ! -d "$SRC" ]]; then
  echo "error: cannot find $SRC" >&2
  exit 1
fi

mkdir -p "$DEST"
if [[ -e "$DEST/ai-film" ]]; then
  echo "note: replacing existing $DEST/ai-film"
  rm -rf "$DEST/ai-film"
fi
cp -R "$SRC" "$DEST/ai-film"

echo "installed -> $DEST/ai-film"
echo
echo "Next:"
echo "  1. In Claude Code, ask for a short film and the skill will load."
echo "  2. Or drive it directly:"
echo "       cd $DEST/ai-film/templates"
echo "       cp shots_template.py shots_myfilm.py"
echo "       ./check_script.py --project myfilm"
echo
command -v ffmpeg >/dev/null || echo "warning: ffmpeg not found on PATH"
command -v ffprobe >/dev/null || echo "warning: ffprobe not found on PATH"
