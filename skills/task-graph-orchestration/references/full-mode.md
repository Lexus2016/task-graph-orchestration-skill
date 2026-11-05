# FULL mode: state machine, checkpoints, reuse, recurring runs

Read this when the mode is FULL, or when work must survive an interruption, recur, or keep watching something for the user.

## State machine

```text
READY → RUNNING → VERIFYING → DONE
VERIFYING → REPAIR → VERIFYING      repair budget left and a new cause to test
REPAIR → FAILED                      budget spent, or the loop SSoT re-look found no new cause
RUNNING | VERIFYING → WAITING        an external operation is still pending
WAITING → VERIFYING                  the operation reached a terminal state
any active state → BLOCKED           missing input, permission or capability
BLOCKED → READY                      the missing item arrived
DONE → STALE → READY                 an upstream input, version or criterion changed
READY → DONE                         the output already exists and passes its check (no run needed)
READY | BLOCKED | RUNNING → SKIPPED  optional unit, or `superseded`: the criteria it served already have evidence
any non-terminal → SKIPPED           the whole completion contract is met (early finish)
```

- **FAILED** records what happened; it needs no permission and must be reported.
- **SKIPPED** is a decision with a reason: `optional`, or `superseded` plus the evidence that made the unit unnecessary. Required criteria, not units, decide completeness: a skipped unit is fine when its criteria are met another way; a required criterion without evidence leaves the request incomplete.
- **Checkpoint** (SKILL.md section 4) runs after every unit result; it is where early finish, skips and replans are decided.
- **STALE** replaces silent reuse: when an input changes, mark exactly the affected descendants STALE and leave unaffected branches DONE.
- The graph has many finished branches at once. Resume from the set of unit statuses, never from a single "last position".

## Checkpoints

Persist state only when an interruption, the run's duration or recurrence makes it pay off. Use the environment's task store or the state file from `state-schema.md`. Never store credentials or unnecessary personal data in it.

Record: goal and completion contract, assumptions, graph version, unit statuses, attempts and causes tested, artifact locations, evidence, pending operation IDs, budget used, authorization scope.

**Resume procedure**

1. Reconcile external operations first: query each pending ID and move WAITING units on.
2. Recheck changed prerequisites and mark affected descendants STALE.
3. Recheck volatile facts and external state that DONE units depend on.
4. Continue from every READY unit.

## Reuse

Reuse a checked artifact only if its inputs, source versions or freshness, code or prompt version, configuration and acceptance criteria are all still compatible. A changed dependency invalidates only its descendants. Never rerun an external write just because its local cache is missing — check the target state instead.

## Discovery details

Give each finding a stable key, a status (accepted or rejected), the reason and the source date. Reconsider a rejected finding only when its evidence or the criteria change. A run of fruitless rounds is a signal to change strategy or report the gap. It never proves completeness.

## Monitoring details

Store for each monitor: the agreed terminal outcome, the deadline or observation window, the cadence and the stop conditions. An unchanged result or an empty check is an observation, not a terminal state. Valid stops: the agreed outcome, cancellation, loss of relevance, the window expiring, or a blocker that needs the user.

## Recurring workflows and run metrics

Reuse a versioned workflow and adapt it to changed constraints. After a material failure, record the observed cause and outcome. Promote a lesson into a rule only when it generalizes or expresses a real invariant. Never silently edit installed skills or standing permissions as a learning step.

Per run, keep the telemetry the environment already reports: elapsed time, repairs and replans per unit, worker and tool calls, cost. At cleanup of each run of a recurring workflow, append one line per unit to the run history (`state-schema.md`, "Run history"). Count, per unit type, how runs actually went — plain frequencies, no probabilistic model — and use them for three decisions:

- **Repair budget:** if, over the last 10 or more occurrences of a unit type, a second repair after a failed first one succeeded at most once, set that type's budget to one repair and escalate on the second failure. If it succeeded in most of them, a budget of two is justified.
- **Bottleneck:** a unit type that needs repairs in run after run → revisit its interface or its check, not the prompt wording.
- **Cost drift:** time or cost rising between like-for-like runs (same acceptance version) → revisit concurrency, batching and reuse.

With fewer than 10 occurrences keep the defaults. History says how often something happened; it never predicts this run's specific failure, so the loop rules and the "new cause per repair" rule still apply inside every run. Never estimate missing telemetry, and don't add measurement to small tasks.
