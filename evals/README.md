# Evals

Each folder is one test case: `prompt.md` (a settings block, then the user's prompt), `case.yaml` (what success looks like), `graders/` (one checkable statement per file), and optional input `files/`.

**Any agent, by hand:** give the agent this skill, copy `files/` into an empty working directory, send the prompt text below the settings block, then judge the response against each file in `graders/`. Repeat without the skill for a baseline. The settings block (`allowed_tools`, `max_turns`) is read only by the Claude Code runner; other runtimes ignore it.

**Benchmark harness (any machine with Claude Code):** `evals/harness/ab-run.sh` runs every case in three arms — `without`, `forced` (skill loaded and requested), `auto` (skill available only) — with clean settings; `ab-judge.py` grades the runs blind; `summarize.py` prints the tables used in the main README. Results of the published run: `benchmark/RESULTS.md`.

**Claude Code runner:** from the repository root, `claude plugin eval . --allow-tools Write Edit Bash --scaffold`.

| Case | Checks |
|---|---|
| `loop-trigger-changes-strategy` | a repeated failure fires SSoT and the next step tests a new cause |
| `final-check-catches-unverified-claim` | the final-decision SSoT catches a worker claim without evidence |
| `direct-task-no-ritual` | a trivial task gets no plan and no state file |
| `batch-with-broken-item` | a small batch with two bad items is reported honestly, not as "all good" |
| `research-conflicting-sources` | five local sources disagree (outdated docs, newer changelog, old blog, forum claim); answer must pick the right two numbers and cite them |
| `programming-multifile-fix` | discount-stacking bug; visible tests miss it, hidden tests (run by code) catch it; a pre-existing unrelated test failure must be reported, not hidden |
| `partly-done-migration` | four of six configs are already migrated and the migration script is not idempotent; only two may be touched (checked byte-for-byte) |
