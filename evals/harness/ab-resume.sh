#!/usr/bin/env bash
# Two-session resume benchmark for Claude Code: session 1 is killed once KILL_AT customer emails have gone out
# (a crash mid-batch); session 2 is a fresh session told to finish the job in the same directory.
# Usage: CASES=refund-batch-resume MODEL=claude-haiku-5-5 ARMS="without forced" bash evals/harness/ab-resume.sh <runs> <conc>
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SP="${BENCH_DIR:-$PWD/.bench}"; REPO="${REPO:-$(cd "$HERE/../.." && pwd -P)}"
mkdir -p "$SP"; [ -f "$SP/empty-mcp.json" ] || echo '{"mcpServers":{}}' > "$SP/empty-mcp.json"
MODEL="${MODEL:-claude-haiku-5-5}"; RUNS="${1:-3}"; CONC="${2:-3}"; OUT="${OUT:-$SP/resume}"
KILL_AT="${KILL_AT:-15}"; S1_TIMEOUT="${S1_TIMEOUT:-420}"
ISO_ROOT="${ISO_ROOT:-$SP/iso}"; mkdir -p "$ISO_ROOT"
mkdir -p "$OUT"

killtree() { local p; for p in $(pgrep -P "$1" 2>/dev/null); do killtree "$p"; done; kill "$1" 2>/dev/null; }

session() {  # wd prompt-file out-jsonl arm
  local extra=() ssot=1; case "$4" in forced*|auto) extra=(--plugin-dir "$REPO") ;; old*) extra=(--plugin-dir "$OLD_PLUGIN") ;; esac; [ "$4" = forcednossot ] && ssot=0
  ( cd "$1" && TGO_AUTO_UPDATE=0 TGO_SSOT=$ssot TGO_SSOT_HISTORY="$1/.ssot-history" exec claude -p --model "$MODEL" --setting-sources project,local \
      --strict-mcp-config --mcp-config "$SP/empty-mcp.json" \
      --allowedTools "Read,Write,Edit,Bash,Glob,Grep,Skill,Task,Agent" --max-turns 80 \
      --output-format stream-json --verbose "${extra[@]}" < "$2" > "$3" 2> "$3.err" )
}

one() {  # case arm n
  local c="$1" arm="$2" n="$3" base="$OUT/$1/$2" wd pid start sent
  if [ -f "$base/run-$n.jsonl" ] && grep -q '"type":"result"' "$base/run-$n.jsonl"; then echo "skip $c $arm $n"; return; fi
  # Isolation: the working directory lives alone under a fresh random parent, so the agent cannot see other runs;
  # base/work-<n> is a symlink to it for the judge.
  mkdir -p "$base"; rm -rf -- "$base/work-$n"
  wd="$(mktemp -d "$ISO_ROOT/r.XXXXXXXX")/shop"; mkdir -p "$wd"; ln -s "$wd" "$base/work-$n"
  cp -R "$REPO/evals/$c/files/." "$wd/"
  awk 'BEGIN{f=0} /^---$/{f++; next} f>=2{print}' "$REPO/evals/$c/prompt.md" | sed '/./,$!d' > "$base/task-$n.txt"
  local pre=""; case "$arm" in forced*|oldforced) pre="${FORCED_PREFIX:-Use the task-graph-orchestration skill for this task.}"$'\n\n' ;; esac
  { printf '%s' "$pre"; cat "$base/task-$n.txt"; } > "$base/s1-prompt-$n.txt"
  { printf '%s' "$pre"; printf 'A previous session was working on the task below in this directory and crashed partway through. Finish the job.\n\nTask:\n'; cat "$base/task-$n.txt"; } > "$base/prompt-$n.txt"
  start=$(date +%s)
  session "$wd" "$base/s1-prompt-$n.txt" "$base/s1-$n.jsonl" "$arm" &
  pid=$!
  while kill -0 "$pid" 2>/dev/null; do
    sent=$( [ -f "$wd/outbox.log" ] && wc -l < "$wd/outbox.log" | tr -d ' ' || echo 0)
    if [ "$sent" -ge "$KILL_AT" ] || [ $(( $(date +%s) - start )) -ge "$S1_TIMEOUT" ]; then killtree "$pid"; echo "killed s1 at $sent emails" > "$base/s1-$n.kill"; break; fi
    sleep 0.5
  done
  wait "$pid" 2>/dev/null
  cp "$wd/outbox.log" "$base/s1-outbox-$n.log" 2>/dev/null || : > "$base/s1-outbox-$n.log"
  session "$wd" "$base/prompt-$n.txt" "$base/run-$n.jsonl" "$arm"
  echo "done $c $arm $n (s1 sent $(wc -l < "$base/s1-outbox-$n.log" | tr -d ' '))"
}
export -f one session killtree; export OUT REPO SP MODEL FORCED_PREFIX KILL_AT S1_TIMEOUT ISO_ROOT OLD_PLUGIN

for c in ${CASES:-refund-batch-resume}; do
  for n in $(seq 1 "$RUNS"); do for arm in ${ARMS:-without forced}; do echo "$c $arm $n"; done; done
done | xargs -P "$CONC" -L 1 bash -c 'one "$0" "$1" "$2"'
echo "ALL DONE"
