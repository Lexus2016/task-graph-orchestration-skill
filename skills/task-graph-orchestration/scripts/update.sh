#!/usr/bin/env bash
# task-graph-orchestration — install and self-update for every local agent.
#
#   bash scripts/update.sh check     # throttled (24h) auto-update; used by the skill itself
#   bash scripts/update.sh update    # check now and update if a newer release exists
#   bash scripts/update.sh install   # copy this checkout into every detected agent skill root
#   bash scripts/update.sh version   # print the installed version
#
# Always exits 0 in check/update mode so it never blocks an agent run.
# Opt out of auto-update: TGO_AUTO_UPDATE=0.
# Output (one line, machine-readable first word):
#   UP-TO-DATE <v> | UPDATED <old> -> <new> | SKIPPED <reason> | DISABLED | INSTALLED <v> -> <paths>

set -u

NAME="task-graph-orchestration"
REPO="${TGO_REPO:-Lexus2016/task-graph-orchestration-skill}"
RAW_VERSION_URL="${TGO_RAW_VERSION_URL:-https://raw.githubusercontent.com/$REPO/main/skills/$NAME/VERSION}"
TARBALL_URL_TEMPLATE="${TGO_TARBALL_URL_TEMPLATE:-https://github.com/$REPO/archive/refs/tags/v%s.tar.gz}"
TTL_SECONDS="${TGO_CHECK_TTL:-86400}"
STATE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/$NAME"

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"

# Skill roots of supported agents. A root counts only if its parent agent is installed (root exists).
ROOTS=(
  "$HOME/.claude/skills"           # Claude Code
  "$HOME/.agents/skills"           # Codex, Gemini CLI, Copilot CLI (shared root)
  "$HOME/.config/opencode/skills"  # OpenCode
)

say() { printf '%s\n' "$*"; }

local_version() { tr -d '[:space:]' < "$SKILL_DIR/VERSION" 2>/dev/null || printf '0.0.0'; }

valid_semver() { printf '%s' "$1" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$'; }

# true if $1 is strictly newer than $2
is_newer() {
  [ "$1" = "$2" ] && return 1
  [ "$(printf '%s\n%s\n' "$1" "$2" | sort -t. -k1,1n -k2,2n -k3,3n | tail -n1)" = "$1" ]
}

# Replace target dir with src dir atomically-enough: build next to it, then swap.
place_copy() {
  local src="$1" target="$2" tmp="$2.new.$$" old="$2.old.$$"
  rm -rf "$tmp" && cp -R "$src" "$tmp" || { rm -rf "$tmp"; return 1; }
  rm -rf "$tmp/.git"
  if [ -e "$target" ]; then mv "$target" "$old" || { rm -rf "$tmp"; return 1; }; fi
  if mv "$tmp" "$target"; then rm -rf "$old"; else [ -e "$old" ] && mv "$old" "$target"; rm -rf "$tmp"; return 1; fi
}

# Copy $1 (a skill dir) into roots. mode=install creates missing copies; mode=update refreshes existing ones.
deploy() {
  local src="$1" mode="$2" root target done_paths="" seen=""
  for root in "${ROOTS[@]}"; do
    [ -d "$root" ] || continue
    target="$root/$NAME"
    if [ -L "$target" ]; then continue; fi            # a symlink follows another copy; leave it
    if [ "$mode" = "update" ] && [ ! -d "$target" ]; then continue; fi
    real="$(cd "$root" && pwd -P)/$NAME"
    case " $seen " in *" $real "*) continue ;; esac
    seen="$seen $real"
    if [ "$(cd "$src" && pwd -P)" = "$real" ]; then done_paths="$done_paths $target"; continue; fi
    place_copy "$src" "$target" && done_paths="$done_paths $target"
  done
  printf '%s' "$done_paths"
}

fetch_release() {   # $1 = version, $2 = empty work dir; prints path of the extracted, validated skill dir
  local ver="$1" work="$2" url dir
  url="$(printf "$TARBALL_URL_TEMPLATE" "$ver")"
  curl -fsSL --max-time 30 "$url" -o "$work/release.tar.gz" || return 1
  tar -xzf "$work/release.tar.gz" -C "$work" || return 1
  dir="$(find "$work" -type f -path "*/skills/$NAME/SKILL.md" | head -n1)"
  [ -n "$dir" ] || return 1
  dir="$(dirname "$dir")"
  grep -Eq "^name: $NAME\$" "$dir/SKILL.md" || return 1
  [ "$(tr -d '[:space:]' < "$dir/VERSION" 2>/dev/null)" = "$ver" ] || return 1
  printf '%s' "$dir"
}

do_update() {   # $1 = throttle (yes|no)
  if [ "${TGO_AUTO_UPDATE:-1}" = "0" ]; then say "DISABLED"; return 0; fi
  local cur remote stamp now work newdir paths
  cur="$(local_version)"
  mkdir -p "$STATE_DIR" 2>/dev/null
  stamp="$STATE_DIR/last-check"
  now="$(date +%s)"
  if [ "$1" = "yes" ] && [ -f "$stamp" ] && [ $((now - $(cat "$stamp" 2>/dev/null || echo 0))) -lt "$TTL_SECONDS" ]; then
    say "UP-TO-DATE $cur (checked within ${TTL_SECONDS}s)"; return 0
  fi
  remote="$(curl -fsSL --max-time 5 "$RAW_VERSION_URL" 2>/dev/null | tr -d '[:space:]')"
  if ! valid_semver "$remote"; then say "SKIPPED offline-or-unreachable ($cur kept)"; return 0; fi
  printf '%s' "$now" > "$stamp" 2>/dev/null
  if ! is_newer "$remote" "$cur"; then say "UP-TO-DATE $cur"; return 0; fi
  work="$(mktemp -d "${TMPDIR:-/tmp}/$NAME.XXXXXX")" || { say "SKIPPED no-temp-dir ($cur kept)"; return 0; }
  newdir="$(fetch_release "$remote" "$work")" || { rm -rf "$work"; say "SKIPPED release-v$remote-invalid-or-unreachable ($cur kept)"; return 0; }
  paths="$(deploy "$newdir" update)"
  # The copy this script runs from may live outside the known roots (e.g. a plugin cache): refresh it too.
  case " $paths " in *" $SKILL_DIR "*) : ;; *) [ -w "$SKILL_DIR" ] && [ ! -d "$SKILL_DIR/../../.git" ] && place_copy "$newdir" "$SKILL_DIR" && paths="$paths $SKILL_DIR" ;; esac
  rm -rf "$work"
  say "UPDATED $cur -> $remote:$paths. The new version applies from the next run."
}

case "${1:-check}" in
  check)   do_update yes ;;
  update)  do_update no ;;
  install) paths="$(deploy "$SKILL_DIR" install)"
           if [ -n "$paths" ]; then say "INSTALLED $(local_version) ->$paths"; else say "SKIPPED no-agent-skill-roots-found"; fi ;;
  version) local_version; echo ;;
  *)       say "usage: update.sh [check|update|install|version]"; exit 2 ;;
esac
exit 0
