"""Convert `opencode run --format json` events into the `claude -p --output-format stream-json` shape.
Usage: python3 -I opencode_to_stream.py <raw.jsonl> <wall_seconds>  > run.jsonl
Only the fields ab-judge.py reads are produced: assistant tool_use blocks and one final result line."""
import json
import sys

raw, wall = sys.argv[1], float(sys.argv[2])
events = []
for line in open(raw, errors="ignore"):
    line = line.strip()
    if not line.startswith("{"):
        continue
    try:
        events.append(json.loads(line))
    except json.JSONDecodeError:
        pass

usage = {"input_tokens": 0, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0, "output_tokens": 0}
cost, steps, texts = 0.0, 0, []
for e in events:
    part = e.get("part") or {}
    if e.get("type") == "tool_use":
        name = part.get("tool", "")
        name = "Skill" if name == "skill" else name
        inp = (part.get("state") or {}).get("input") or {}
        print(json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": name, "input": inp}]}}))
    elif e.get("type") == "step_finish":
        steps += 1
        t = part.get("tokens") or {}
        cache = t.get("cache") or {}
        usage["input_tokens"] += t.get("input") or 0
        usage["output_tokens"] += (t.get("output") or 0) + (t.get("reasoning") or 0)
        usage["cache_read_input_tokens"] += cache.get("read") or 0
        usage["cache_creation_input_tokens"] += cache.get("write") or 0
        cost += part.get("cost") or 0
    elif e.get("type") == "text" and part.get("text"):
        texts.append(part["text"])
        print(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": part["text"]}]}}))

print(json.dumps({"type": "result", "subtype": "success" if texts else "error", "result": texts[-1] if texts else "",
                  "duration_ms": int(wall * 1000), "num_turns": steps, "total_cost_usd": cost, "usage": usage}))
