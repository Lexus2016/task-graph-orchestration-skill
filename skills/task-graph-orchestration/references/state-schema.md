# State file

Read this before creating or resuming a state file. Prefer the environment's own task store when it can hold the same fields; use this file otherwise.

## Location and writing rules

- Path: `.orchestration/<goal-slug>.json` in the project root (or the scratch directory for work outside a project). Keep it out of commits unless the user wants it tracked.
- **Single writer:** only the orchestrator writes the file. Workers return their RETURN block and the orchestrator records it.
- Write atomically: write `<file>.tmp`, then rename over the original.
- Bump `graph_version` on every material graph change and note why in `changes`.
- No secrets, tokens or unnecessary personal data. Reference them by vault name only.

## Schema (example)

```json
{
  "goal": "Migrate 40 services from config v1 to v2, one PR each",
  "mode": "FULL",
  "graph_version": 3,
  "completion_contract": [
    {"id": "c1", "text": "Every service loads v2 config and its test suite passes", "required": true},
    {"id": "c2", "text": "One PR per service, linked in the report", "required": true},
    {"id": "c3", "text": "Changelog entry per service", "required": false}
  ],
  "assumptions": ["Services without a test suite are verified by a boot smoke test"],
  "authorization": {"allowed": ["edit service repos", "open PRs to org repos"], "needs_approval": ["merge", "deploy"]},
  "budget": {"max_workers": 3, "repairs_per_unit": 1, "used": {"worker_calls": 41, "repairs": 6}},
  "units": {
    "svc-017": {
      "status": "REPAIR",
      "owner": "worker-2",
      "effect": "reversible write",
      "depends": ["loader-shim"],
      "attempts": [
        {"n": 1, "cause_tested": "v2 key names", "result": "fail", "signature": "KeyError: db.url"},
        {"n": 2, "cause_tested": "custom loader bypasses shim", "result": "pending"}
      ],
      "artifacts": ["branch: migrate/svc-017"],
      "evidence": [],
      "ssot": [{"trigger": "loop", "outcome": "shared assumption: default loader; switched to shim unit"}]
    },
    "svc-021": {
      "status": "WAITING",
      "pending_op": {"kind": "ci_run", "id": "run/88231", "next_check": "2026-11-06T09:00Z"}
    },
    "integration": {
      "status": "WAITING",
      "pending_op": {"kind": "local_process", "id": "pid:48211", "log": ".orchestration/integration.log", "next_check": "on resume"}
    }
  },
  "started": [
    {"kind": "worker", "id": "worker-2"},
    {"kind": "process", "id": "pid:48211"},
    {"kind": "schedule", "id": "check-ci-0900", "keep": "live commitment: CI result for svc-021"},
    {"kind": "worktree", "id": "../wt-svc-017"}
  ],
  "changes": [
    {"graph_version": 3, "why": "added loader-shim unit after svc-017 loop"}
  ],
  "updated_at": "2026-11-05T21:14Z"
}
```

`started` lists everything this run launched (workers, processes, schedules, worktrees, ports) so the cleanup step can stop each one; `keep` marks an item that serves a live user commitment. `pending_op.id` holds whatever identifies the operation — a remote run ID or `pid:<n>` with its `log` path.

## Run history (recurring workflows only)

The state file describes one run and is overwritten by the next; the run history survives across runs. Append-only `.orchestration/history/<workflow>.jsonl`, one line per unit per run, written by the orchestrator at cleanup:

```json
{"run": "2026-11-05", "workflow": "config-v2-migration", "acceptance_version": 2, "unit_type": "service-migration", "unit": "svc-017", "repairs": 2, "final": "DONE", "causes_tested": ["v2 key names", "custom loader bypasses shim"]}
```

Compare only lines with the same `workflow` and `acceptance_version`. Never rewrite past lines; a correction is a new line.

## Minimal fields

Fields not needed by a run can be dropped; `goal`, `completion_contract`, `units.*.status` and pending operation IDs are the minimum for a working resume.
