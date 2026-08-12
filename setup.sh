#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$HOME/.claude/skills/grant-compass"
SRC="$SCRIPT_DIR/.claude/skills/grant-compass"

mkdir -p "$HOME/.claude/skills"

if [ -L "$TARGET" ] && [ "$(readlink "$TARGET")" = "$SRC" ]; then
  echo "grant-compass already linked at $TARGET"
elif [ -e "$TARGET" ]; then
  echo "Skipping: $TARGET already exists and is not our symlink."
else
  ln -s "$SRC" "$TARGET"
  echo "Linked $TARGET -> $SRC"
fi

echo "Next: pip install -e \"$SCRIPT_DIR\" (or 'pip install -r requirements.txt' + run with PYTHONPATH=src)"
echo "Then: grantcompass init   # scaffolds config.local.yaml"
