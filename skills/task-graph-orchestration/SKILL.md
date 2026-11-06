---
name: task-graph-orchestration
description: Keeps multi-step agent work honest and unstuck. Breaks repeated-failure loops, verifies claims (from subagents, tools, CI, logs, a previous session, or your own memory) before you report or build on them, resumes interrupted work without repeating irreversible actions, and plans dependent work only when it pays. Use when the same fix has failed twice or attempts keep repeating; before a final report or "done" that rests on someone else's claims or on numbers and checks you have not just run; when finishing a crashed, interrupted or half-done batch; for batches where some items may fail; and for fan-out to parallel subagents. Not for single edits, lookups or short obvious sequences.
compatibility: Runtime-agnostic (any agent that reads Markdown instructions). Optional helper scripts need Python 3.
---
# Task graph orchestration

Deliver an accepted result with the least extra work. Every rule here fixes a failure measured in agent runs; nothing is ceremony. **One action or a short obvious sequence? Just do it and stop reading.**

## 1. Before acting

- **Completion contract:** 2–6 checkable criteria taken from the request, each `required` or `optional`. It is your definition of done; keep assumptions apart and disclose them. A new request from the user mid-work gets its own 2–6 criteria, added before you continue and checked in the final answer.
- **Plan only real dependencies.** A unit is a deliverable with a check, never a single tool call. N similar items are **one** unit whose check counts or diffs the outputs.
- Look only in the working directory and the places the request names. If verifying a claim needs access you do not have, label it unverified in the answer — do not go looking elsewhere for it.

## 2. Evidence — where agents actually fail

- **Done means a check you ran in this session passed.** Visible tests passing is not the spec being met: check each spec item the tests do not cover. For anything a person will look at, open it the way they will (each language, role and state that changed) before saying done; if you cannot, check what it renders from (translation catalogs, templates, config) for the changed parts. If neither is done, the headline says "done except X", never plain "done".
- **A claim is not evidence.** A worker's report, a log line, a CI badge, a previous session's notes and your memory of having checked are claims. Open the artifact — file, output, receipt — before relying on it.
- **Every number you state comes from a command that counted exactly what you name.** Before the final answer, list the counts you are about to give and print each with its own command (`wc -l`, `grep -c`, `len(...)`). Never count lines of output or list items by eye, and never name a category ("rows with a decimal comma") you did not count on its own: a script that fixes things should print how many it fixed of each kind.
- **Irreversible actions** (emails, payments, deploys, deletions): read the authoritative record of what already happened, act only on the remainder, then re-read it to confirm. A gap in the record is a reason to inspect, not to stop: once the record answers the question, proceed. For a running system, first read how it is actually run now (running config, container labels, the live vhost), not how the repo or docs say it is run, and change it only through that same path.
- **No probe records in a live system.** Test the API with read calls or the data you were given; if a write test is unavoidable, delete the record and say so in the answer.
- Verify with the cheapest check that can fail: an independent recomputation for numbers, a diff against expected output for transforms, the receipt for side effects.

## 3. Loops — never a third try of the same idea

Keep a one-line failure ledger in your notes: `attempt → cause tested → result`. When the same error appears twice, or you are about to test a cause already in the ledger, run a **loop SSoT** (below): list the attempts, name the assumption they all share, then test a different cause or change strategy — or stop and report with the evidence. A plain retry is not an outcome.

## 4. SSoT — step outside your own reasoning

A short deliberate pause that breaks the inertia of your first interpretation, then a re-look from a forced angle.

1. Write 10 letters and digits yourself — mixed case, at least two digits, new every time. Never reuse, adapt or copy a string you have seen (including examples).
2. `pos = (sum of the digits) mod 10`, 0-indexed; `char = string[pos]`.
3. Note `SSoT: {string} (digit-sum {S}, pos {N}): {char}.`
4. **Angle** = `pos mod 5`: 0 **user** — would the person who asked accept this? · 1 **spec** — which requirement is not covered by evidence? · 2 **edge** — which input breaks it (empty, zero, max, duplicate, timezone, unicode, failure)? · 3 **reviewer** — what is the most likely way this is wrong? · 4 **next** — could someone continue from the artifacts alone?
5. If this angle is the same as your previous SSoT in this task, take the next one (`(angle+1) mod 5`): a string composed from habit locks you into one angle.
6. Answer the angle with a concrete fact (file, line, command output). If it exposes a problem, act on it before moving on. Never recompose the string to get a different angle or to dismiss what the angle found.

**When:** a loop (section 3); a **commitment** — before you settle on a root cause, an interpretation of the spec or an approach the rest of the work depends on; **done** on a unit whose effect cannot be undone or that no automated check covers; the **final decision** — before the final answer on non-trivial work and before any irreversible action — concretely, before the first command in a batch that changes something outside the working directory (ssh/scp/rsync, docker/compose, git push or merge, a database write, a deploy script), once per batch; and whenever the user writes "SSoT". Several triggers at once make one checkpoint, not several. Not on every step: a pause on everything is no pause. Standing user or project rules that add triggers take precedence. SSoT lines are working notes — keep them out of the final answer unless the user asked for them.

## 5. Parallel work — only when it pays

Delegate only independent units with heavy reading or long runtimes. Brief = goal, paths (not contents), constraints, forbidden actions, return format. Ask for a return of at most ~15 lines: conclusion, evidence paths, open issues. One owner per mutable output; parallel code edits go to separate worktrees or disjoint files. A worker's return is a claim — section 2 applies.

## 6. Final answer

Before sending, check silently: every required criterion has evidence or is named as a gap; numbers were computed; claims were verified; nothing irreversible happened twice; open or pending items are listed. Then answer about the work, not about this skill: lead with the result, give the evidence that matters, state gaps plainly. No plans, modes or SSoT lines unless asked.

## Long, resumable or recurring work

When the work must survive this session (overnight runs, multi-session batches, recurring jobs), keep state on disk: `scripts/tgo.py` is a small state machine (plan, start, done with a check, failure ledger, final) and `references/full-mode.md` covers checkpoints, resume and monitoring. Keep units coarse; one unit per item turns the graph into overhead. `references/runtime-adapter.md` maps workers, waits and cleanup onto runtimes without these capabilities.
