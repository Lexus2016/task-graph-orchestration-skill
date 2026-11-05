#!/usr/bin/env bash
# A/B runner for OpenCode: each eval case × arms × N runs, headless `opencode run`, isolated config.
# Usage: MODEL=ollama-cloud/deepseek-v4.1-flash:1017 ARMS="without forced auto" \
#        [CASES="case-a case-b"] [FORCED_PREFIX="..."] bash evals/harness/ab-run-opencode.sh <runs> <concurrency>
# Isolation: HOME and XDG_CONFIG_HOME point to an empty sandbox, so no global AGENTS.md, CLAUDE.md, plugins or
# other skills are loaded; XDG_DATA_HOME stays real so provider auth (auth.json) keeps working.
# Output is converted to the same stream-json shape as `claude -p`, so ab-judge.py grades both runtimes.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO="${REPO:-$(cd "$HERE/../.." && pwd -P)}"
SP="${BENCH_DIR:-$PWD/.bench}"
OUT="${OUT:-$SP/ab-opencode}"
MODEL="${MODEL:-ollama-cloud/deepseek-v4.1-flash:1017}"
RUN_TIMEOUT="${RUN_TIMEOUT:-600}"
RUNS="${1:-3}"; CONC="${2:-4}"
REAL_DATA="${XDG_DATA_HOME:-$HOME/.local/share}"; REAL_CACHE="${XDG_CACHE_HOME:-$HOME/.cache}"
mkdir -p "$OUT"
ISO_ROOT="${ISO_ROOT:-$SP/iso}"; mkdir -p "$ISO_ROOT"; OLD_PLUGIN="${OLD_PLUGIN:-}"

one() {  # case arm n
  local c="$1" arm="$2" n="$3" base="$OUT/$1/$2" wd iso start pid
  iso="$base/iso-$n"
  if [ -f "$base/run-$n.jsonl" ] && grep -qE '"type": ?"result"' "$base/run-$n.jsonl"; then echo "skip $c $arm $n"; return; fi
  case "$iso" in "$OUT"/*) rm -rf -- "$iso" ;; esac
  mkdir -p "$base"; rm -rf -- "$base/work-$n"   # isolated workdir under a random parent; symlinked for the judge
  wd="$(mktemp -d "$ISO_ROOT/r.XXXXXXXX")/work"; ln -s "$wd" "$base/work-$n"
  mkdir -p "$wd" "$iso/home" "$iso/config/opencode" "$iso/state"
  printf '{"$schema":"https://opencode.ai/config.json","permission":{"*":"allow","skill":{"*":"allow"}}}\n' \
    > "$iso/config/opencode/opencode.json"
  case "$arm" in forced|auto)
    mkdir -p "$iso/config/opencode/skills"
    cp -R "$REPO/skills/task-graph-orchestration" "$iso/config/opencode/skills/" ;;
  old*)
    mkdir -p "$iso/config/opencode/skills"
    cp -R "$OLD_PLUGIN/skills/task-graph-orchestration" "$iso/config/opencode/skills/" ;;
  esac
  [ -d "$REPO/evals/$c/files" ] && cp -R "$REPO/evals/$c/files/." "$wd/"
  awk 'BEGIN{f=0} /^---$/{f++; next} f>=2{print}' "$REPO/evals/$c/prompt.md" | sed '/./,$!d' > "$base/prompt-$n.txt"
  if [ "$arm" = "forced" ] || [ "$arm" = "oldforced" ]; then
    { printf '%s\n\n' "${FORCED_PREFIX:-Use the task-graph-orchestration skill for this task.}"; cat "$base/prompt-$n.txt"; } > "$base/p.tmp-$n" \
      && mv "$base/p.tmp-$n" "$base/prompt-$n.txt"
  fi
  start=$(date +%s)
  ( cd "$wd" && env HOME="$iso/home" XDG_CONFIG_HOME="$iso/config" XDG_STATE_HOME="$iso/state" \
      XDG_DATA_HOME="$REAL_DATA" XDG_CACHE_HOME="$REAL_CACHE" TGO_AUTO_UPDATE=0 \
      opencode run --standalone --auto --format json -m "$MODEL" "$(cat "$base/prompt-$n.txt")" < /dev/null \
      > "$base/raw-$n.jsonl" 2> "$base/run-$n.err" ) &
  pid=$!
  while kill -0 "$pid" 2>/dev/null; do
    [ $(( $(date +%s) - start )) -ge "$RUN_TIMEOUT" ] && { pkill -P "$pid" 2>/dev/null; kill "$pid" 2>/dev/null; echo "TIMEOUT" >> "$base/run-$n.err"; break; }
    sleep 2
  done
  python3 -I "$HERE/opencode_to_stream.py" "$base/raw-$n.jsonl" $(( $(date +%s) - start )) > "$base/run-$n.jsonl"
  echo "done $c $arm $n"
}
export -f one; export OUT REPO MODEL RUN_TIMEOUT HERE REAL_DATA REAL_CACHE FORCED_PREFIX ISO_ROOT OLD_PLUGIN

for c in ${CASES:-$(ls "$REPO/evals")}; do
  [ -f "$REPO/evals/$c/prompt.md" ] || continue
  for n in $(seq 1 "$RUNS"); do for arm in ${ARMS:-without forced auto}; do echo "$c $arm $n"; done; done
done | xargs -P "$CONC" -L 1 bash -c 'one "$0" "$1" "$2"'
echo "ALL DONE"
