#!/usr/bin/env bash
# A/B runner: each eval case × {with, without} skill × N runs, headless `claude -p`, clean settings.
# Usage: MODEL=claude-haiku-5-5 ARMS="without forced auto" bash evals/harness/ab-run.sh <runs> <concurrency>
# Results: $BENCH_DIR/ab/<case>/<arm>/run-<n>.jsonl  (BENCH_DIR defaults to ./.bench)
# Arms: without = no skill; forced = skill loaded + "Use the task-graph-orchestration skill"; auto = skill available only.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SP="${BENCH_DIR:-$PWD/.bench}"
REPO="${REPO:-$(cd "$HERE/../.." && pwd -P)}"
mkdir -p "$SP"; [ -f "$SP/empty-mcp.json" ] || echo '{"mcpServers":{}}' > "$SP/empty-mcp.json"
MODEL="${MODEL:-claude-opus-5-5}"
RUNS="${1:-3}"; CONC="${2:-4}"
OUT="${OUT:-$SP/ab}"
mkdir -p "$OUT"
ISO_ROOT="${ISO_ROOT:-$SP/iso}"; mkdir -p "$ISO_ROOT"; OLD_PLUGIN="${OLD_PLUGIN:-}"

one() {  # case arm n
  local c="$1" arm="$2" n="$3" base="$OUT/$1/$2" wd
  if [ -f "$base/run-$n.jsonl" ] && grep -q '"type":"result"' "$base/run-$n.jsonl"; then echo "skip $c $arm $n"; return; fi
  mkdir -p "$base"; rm -rf -- "$base/work-$n"   # isolated workdir under a random parent; symlinked for the judge
  wd="$(mktemp -d "$ISO_ROOT/r.XXXXXXXX")/work"; mkdir -p "$wd"; ln -s "$wd" "$base/work-$n"
  [ -d "$REPO/evals/$c/files" ] && cp -R "$REPO/evals/$c/files/." "$wd/"
  # prompt = prompt.md without its leading settings block
  awk 'BEGIN{f=0} /^---$/{f++; next} f>=2{print}' "$REPO/evals/$c/prompt.md" | sed '/./,$!d' > "$base/prompt-$n.txt"
  local extra=()
  case "$arm" in forced|auto) extra=(--plugin-dir "$REPO") ;; old*) extra=(--plugin-dir "$OLD_PLUGIN") ;; esac
  if [ "$arm" = "forced" ] || [ "$arm" = "oldforced" ]; then
    { printf '%s\n\n' "${FORCED_PREFIX:-Use the task-graph-orchestration skill for this task.}"; cat "$base/prompt-$n.txt"; } > "$base/prompt-$n.tmp" && mv "$base/prompt-$n.tmp" "$base/prompt-$n.txt"
  fi
  ( cd "$wd" && TGO_AUTO_UPDATE=0 claude -p --model "$MODEL" --setting-sources project,local \
      --strict-mcp-config --mcp-config "$SP/empty-mcp.json" \
      --allowedTools "Read,Write,Edit,Bash,Glob,Grep,Skill,Task,Agent" --max-turns "$(awk '/^max_turns:/{print $2; exit}' "$REPO/evals/$c/prompt.md" || echo 20)" \
      --output-format stream-json --verbose "${extra[@]}" \
      < "$base/prompt-$n.txt" > "$base/run-$n.jsonl" 2> "$base/run-$n.err" )
  echo "done $c $arm $n"
}
export -f one; export OUT REPO SP MODEL FORCED_PREFIX ISO_ROOT OLD_PLUGIN

for c in ${CASES:-$(ls "$REPO/evals" | grep -v -e README -e results)}; do
  [ -f "$REPO/evals/$c/prompt.md" ] || continue
  for n in $(seq 1 "$RUNS"); do for arm in ${ARMS:-without forced auto}; do echo "$c $arm $n"; done; done
done | xargs -P "$CONC" -L 1 bash -c 'one "$0" "$1" "$2"'
echo "ALL DONE"
