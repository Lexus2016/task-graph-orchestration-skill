#!/usr/bin/env bash
# Install task-graph-orchestration into every local agent that has a skills folder
# (Claude Code, Codex / Gemini CLI / Copilot CLI via ~/.agents/skills, OpenCode)
# and schedules a daily update check (TGO_AUTO_UPDATE=0 to skip).
#   curl -fsSL https://raw.githubusercontent.com/Lexus2016/task-graph-orchestration-skill/main/install.sh | bash
set -eu
REPO="Lexus2016/task-graph-orchestration-skill"
NAME="task-graph-orchestration"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd -P || true)"
if [ -n "$HERE" ] && [ -f "$HERE/skills/$NAME/scripts/update.sh" ]; then
  bash "$HERE/skills/$NAME/scripts/update.sh" install
  bash "$HERE/skills/$NAME/scripts/update.sh" schedule
  exit 0
fi
VER="$(curl -fsSL "https://raw.githubusercontent.com/$REPO/main/skills/$NAME/VERSION" | tr -d '[:space:]')"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/$NAME.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
curl -fsSL "https://github.com/$REPO/archive/refs/tags/v$VER.tar.gz" | tar -xz -C "$WORK"
SRC="$(find "$WORK" -type f -path "*/skills/$NAME/scripts/update.sh" | head -n1)"
[ -n "$SRC" ] || { echo "release v$VER has no skill"; exit 1; }
bash "$SRC" install
# Schedule from the installed copy, not from the temp download.
for root in "$HOME/.claude/skills" "$HOME/.agents/skills" "$HOME/.config/opencode/skills"; do
  [ -f "$root/$NAME/scripts/update.sh" ] && { bash "$root/$NAME/scripts/update.sh" schedule; break; }
done
echo "Restart your agent to load the skill. Opt out of daily updates: bash <skill>/scripts/update.sh unschedule"
