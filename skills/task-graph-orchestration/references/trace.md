# Graph trace and replay

Read this in FULL mode, or when the user or the operator asks to trace a LITE run ("trace the graph", "show me the task map", `TGO_TRACE=1`). Never trace DIRECT work. A trace records the task graph and every change to it, so the run can be replayed as an animated map and checked against this skill. It adds no new steps: it writes down what the skill already asks you to decide.

## File

Append-only JSON Lines at `.orchestration/<goal-slug>.trace.jsonl` in the working directory. One event per line. Batch the events of one moment into a single append (`cat >> file <<'EOF' … EOF`) together with the action that caused them — never spend a separate tool call on the trace alone. Never rewrite past lines. Workers do not write the trace; the orchestrator records their delegation and return.

Every event has `"seq"` (1, 2, 3 … in write order) and `"ev"`. Keep strings short — this is a map, not a log of contents.

## Events

```jsonl
{"seq":1,"ev":"plan","mode":"LITE|FULL","goal":"…","criteria":[{"id":"c1","text":"…","required":true}],"units":[{"id":"u1","title":"…","depends":[],"criteria":["c1"],"effect":"read-only|reversible|consequential","owner":"self|worker"}]}
{"seq":2,"ev":"status","unit":"u1","to":"RUNNING"}
{"seq":3,"ev":"delegate","unit":"u2","worker":"w1","brief_chars":640,"paths":["contracts/a.md"]}
{"seq":4,"ev":"return","unit":"u2","worker":"w1","status":"done","return_chars":410}
{"seq":5,"ev":"evidence","unit":"u1","criterion":"c1","kind":"file|command|test|source|receipt","ref":"report.md line 3"}
{"seq":6,"ev":"status","unit":"u1","to":"DONE"}
{"seq":7,"ev":"checkpoint","after":"u1","decision":"continue|stop|skip|replan","reason":"…"}
{"seq":8,"ev":"skip","unit":"u4","reason":"optional|superseded","by":"c2 already evidenced by u3"}
{"seq":9,"ev":"replan","reason":"…","add":[{"id":"u5","title":"…","depends":["u2"],"cause":"what this unit will test"}],"remove":["u3"],"stale":["u6"]}
{"seq":12,"ev":"failure","unit":"u2","signature":"KeyError: db.url","cause":"v2 key names","next":"test the loader path instead"}
{"seq":10,"ev":"ssot","trigger":"loop|final|user","line":"SSoT: …","outcome":"…"}
{"seq":11,"ev":"final","result":"complete|incomplete","gaps":["c3: no evidence"]}
```

- `status` values are the skill's statuses: READY, RUNNING, VERIFYING, DONE, REPAIR, WAITING, BLOCKED, STALE, FAILED, SKIPPED.
- Record `evidence` before the `status … DONE` it justifies. For a delegated unit, write `return`, then — after checking the worker's evidence — `evidence` and `status DONE` (or FAILED).
- Before `final` with `result: complete`, every required criterion needs an `evidence` event.
- Write a `checkpoint` after every unit result, as section 4 of SKILL.md requires.
- Write a `failure` for every failed attempt — this is the failure ledger. A later `failure` or replanned unit with the same `cause` is flagged as a repeat; the same `signature` twice needs a loop `ssot` in between.
- `brief_chars` / `return_chars`: the length of the brief you sent and of the answer you got back.

## Replay

At the end, `python3 scripts/trace_graph.py render <absolute path to the trace>` (run from the skill's directory) writes `<goal-slug>.graph.html` next to the trace and prints its `file://` link plus the findings of its checks. The page plays the graph from the first plan to the final event: pause, step, drag the slider, or jump to any graph version (v1 = plan, v2… = each replan); `#step=N` in the URL opens a given step. Put the link at the end of your answer.

Checks it runs: plan first; no cause tested twice and no replan back to a failed cause; a loop SSoT between two identical failures; DONE only after evidence; a checkpoint (or replan) after every unit result; skips carry a reason; a final-decision SSoT before `final`; `complete` only when every required criterion has evidence; no unit left open; briefs and returns kept small. Operators can add the run transcript (`--transcript`) to tie events to real tool calls and split token use between the orchestrator and its workers; `trace_graph.py analyze` compares several runs.
