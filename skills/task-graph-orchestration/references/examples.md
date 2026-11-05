# Worked examples

Read this when unsure which mode fits or how much to write down.

## DIRECT — "rename `retryCount` to `maxRetries` in `client.ts` and run the tests"

No plan, no state, no SSoT (nothing consequential). Edit, run the relevant tests, report: "Renamed in 4 places; `npm test client` — 23/23 passed."

## LITE — "compare Qdrant, Weaviate and pgvector for our 5M-vector workload, with sources"

```text
MODE / GOAL: LITE — recommendation for a 5M-vector, self-hosted workload
COMPLETION CONTRACT: required — 3 engines × {filtering, memory at 5M, ops burden, license}, each cell backed
  by a quoted passage dated within 12 months; required — one recommendation with its trade-off;
  optional — cost table
UNITS: 3 research units in parallel (one per engine) → 1 synthesis unit
CHECKS: passage supports the cell; date checked; conflicting benchmarks noted, not averaged
AUTHORIZATION: read-only
```

Final-decision SSoT before sending:

```text
SSoT: hN5r2KpW0e (digit-sum 7, pos 7): W.
Re-look: memory cell for Weaviate cites a 2023 blog — outside the 12-month rule. Replaced with the
current docs passage; recommendation unchanged. All 12 cells mapped to passages.
```

## FULL — "migrate all 40 services from config v1 to v2, one PR each; continue tomorrow if it doesn't finish"

- Units: one per service plus an `integration` unit; `EFFECT: reversible write` (branches), PR opening within the granted org scope, merge and deploy need approval.
- Workers = min(cap 3, READY units, what one integrator can verify) → 3.
- State file `.orchestration/config-v2-migration.json` (see `state-schema.md`).

Loop trigger on `svc-017`: attempt 1 and attempt 2 both end in `KeyError: db.url`.

```text
SSoT: Rb7xQ2mT4z (digit-sum 13, pos 3): x.
Re-look: both attempts edited key names, assuming svc-017 uses the default loader. It uses a custom
loader that bypasses the v2 shim. New unit `loader-shim`; svc-017 now depends on it. No third retry
of the same cause.
```

Final-decision SSoT before the report:

```text
SSoT: Kd3m9Vw1Lp (digit-sum 13, pos 3): m.
Re-look: 37 workers reported "tests pass"; 3 returns had no CI run ID. Checked those 3 directly —
svc-031 fails on CI. Report: 36 DONE with CI links, svc-031 FAILED (cause and log), svc-021 WAITING
(run/88231, next check 09:00), svc-040 BLOCKED (repo access). Merge awaits approval.
```

Cleanup: 3 workers stopped, the scheduled 09:00 check kept (live commitment), state file final.
