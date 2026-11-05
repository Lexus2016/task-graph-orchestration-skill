<p align="center">
  <img src="assets/social-preview.png" alt="task-graph-orchestration — your agent says done, make it prove it" width="820">
</p>

<h1 align="center">task-graph-orchestration</h1>

<p align="center"><b>Your agent says “done”. This skill makes it prove it.</b></p>

<p align="center">
  <a href="LICENSE"><img alt="MIT" src="https://img.shields.io/badge/license-MIT-blue"></a>
  <img alt="version" src="https://img.shields.io/badge/version-1.2.0-informational">
  <img alt="Claude Code" src="https://img.shields.io/badge/Claude%20Code-skill%20%2B%20plugin-d97757">
  <img alt="Codex" src="https://img.shields.io/badge/Codex-skill-111111">
  <img alt="OpenCode" src="https://img.shields.io/badge/OpenCode-skill-4b5563">
  <a href="#benchmark"><img alt="benchmark" src="https://img.shields.io/badge/discipline%20tasks-%2B6..13%20pp%20quality-brightgreen"></a>
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.uk.md">Українська</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a>
</p>

---

On tasks where agents cut corners — repeated failures, reports built on subagent claims — it raises blind-judged quality by **+6 to +13 percentage points** on Haiku, Sonnet, Opus and DeepSeek, for **×1.3–1.5** the cost. [Benchmark ↓](#benchmark)

One drop-in skill for **Claude Code, Codex and OpenCode** that changes how an agent runs anything bigger than a one-liner:

- **Proof, not prose.** A worker saying “tests pass” is a claim. The skill makes the agent check the CI run, the file, the receipt.
- **No blind retries.** Two identical failures in a row trigger **SSoT**: stop, name the assumption every attempt shared, change the cause — or escalate.
- **A second look before “done”.** Before the final report the agent re-reads its own result as a reviewer who didn’t write it.
- **Finish early, skip what's done.** After every step the agent checks the whole plan: goal already met → stop; work already in place → mark it done instead of redoing it; plan wrong → replan only the broken part.
- **Delegate only when it pays.** Narrow first (headings, keywords, a short script), then read; hand work to subagents only when the reading they absorb outweighs their startup cost — with a minimal brief (paths, not contents) and a bounded answer.
- **See the run, not just the result.** Long runs end with a link to an animated replay of the task graph — every plan, replan, skip, checkpoint and SSoT — plus automatic checks of how the agent followed the method.
- **Small stays small.** A rename stays a rename: no plans, no ceremony. Orchestration switches on only when the work needs it.

## Install

**Paste into your agent** (Claude Code, Codex, OpenCode):

```text
Install the agent skill from https://github.com/Lexus2016/task-graph-orchestration-skill —
run its install.sh, show me the INSTALLED line, and tell me to restart you.
```

**One line in a terminal:**

```bash
curl -fsSL https://raw.githubusercontent.com/Lexus2016/task-graph-orchestration-skill/main/install.sh | bash
```

**Claude Code plugin:**

```text
/plugin marketplace add Lexus2016/task-graph-orchestration-skill
/plugin install task-graph-orchestration@task-graph-orchestration
```

The installer copies `skills/task-graph-orchestration/` into every agent skills folder it finds — `~/.claude/skills`, `~/.agents/skills` (Codex, Gemini CLI, Copilot CLI), `~/.config/opencode/skills` — and nothing else. Restart the agent afterwards.

## Benchmark

Measured on 2026-11-05 with skill v1.1.0: Claude Code 2.1.318 (`claude -p`) for Claude models, OpenCode 2.1.2 (`opencode run`) for DeepSeek V4.1 Flash. Every run starts in a fresh directory with clean settings: no user `CLAUDE.md` / `AGENTS.md`, no MCP servers, no other skills.

- **7 tasks in 3 groups.** *Discipline:* a fix that failed twice with the same error; a final report built on three subagent claims, one without evidence. *Real work:* research over five sources that disagree; a discount bug across several files with hidden tests; a migration a teammate half-finished, with a non-idempotent script. *Small:* checking four configs; renaming one function.
- **3 arms.** *without* — no skill · *loaded* — skill installed and the prompt asks for it · *auto* — skill installed, the model decides.
- **Scoring.** A blind judge (Sonnet 5.5) never sees the arm; skill mentions are redacted. It scores quality 1–10 (shown here as % of ideal) and grades every criterion. Hidden tests, untouched files, config values and SSoT arithmetic are checked by code.
- **Runs per arm per task:** Haiku 5, DeepSeek 3, Sonnet 2, Opus 2 — 252 runs in total.

**Discipline tasks (repeated failure, report built on subagent claims)** — quality, % of ideal

| Model | Without skill | Skill loaded | Δ | Relative | Skill auto | Δ |
|---|---|---|---|---|---|---|
| Haiku 5.5 | 60% | 66% | **+6 pp** | +10% | 62% | +2 pp |
| Sonnet 5.5 | 62% | 70% | **+8 pp** | +12% | 60% | -2 pp |
| Opus 5.5 | 62% | 72% | **+10 pp** | +16% | 65% | +2 pp |
| DeepSeek V4.1 Flash (OpenCode) | 62% | 75% | **+13 pp** | +22% | 65% | +3 pp |

**Real work (research with conflicting sources, multi-file bug fix, half-finished migration)** — quality, % of ideal

| Model | Without skill | Skill loaded | Δ | Relative | Skill auto | Δ |
|---|---|---|---|---|---|---|
| Haiku 5.5 | 89% | 89% | **+1 pp** | +1% | 90% | +1 pp |
| Sonnet 5.5 | 87% | 90% | **+3 pp** | +4% | 82% | -5 pp |
| Opus 5.5 | 88% | 85% | **-3 pp** | -4% | 85% | -3 pp |
| DeepSeek V4.1 Flash (OpenCode) | 90% | 86% | **-4 pp** | -5% | 89% | -1 pp |

**Small tasks (should stay small)** — quality, % of ideal

| Model | Without skill | Skill loaded | Δ | Relative | Skill auto | Δ |
|---|---|---|---|---|---|---|
| Haiku 5.5 | 89% | 87% | **-2 pp** | -2% | 90% | +1 pp |
| Sonnet 5.5 | 90% | 88% | **-2 pp** | -3% | 85% | -5 pp |
| Opus 5.5 | 90% | 82% | **-8 pp** | -8% | 90% | +0 pp |
| DeepSeek V4.1 Flash (OpenCode) | 90% | 87% | **-3 pp** | -4% | 88% | -2 pp |

**Cost of using the skill** — all non-small tasks, *without → loaded*

| Model | Time | Tool calls | Tokens | of them cache reads | Uncached input + output | Cost |
|---|---|---|---|---|---|---|
| Haiku 5.5 | ×2.8 | 3.6 → 6.2 | ×1.9 | 88% → 91% | ×1.4 | ×1.5 ($0.0030 → $0.0047) |
| Sonnet 5.5 | ×1.0 | 1.8 → 4.7 | ×1.8 | 87% → 91% | ×1.2 | ×1.3 ($0.0379 → $0.0497) |
| Opus 5.5 | ×1.4 | 1.5 → 2.7 | ×1.8 | 86% → 90% | ×1.2 | ×1.3 ($0.0768 → $0.0997) |
| DeepSeek V4.1 Flash (OpenCode) | ×1.6 | 7.1 → 7.5 | ×1.7 | 73% → 72% | ×1.7 | ×1.5 ($0.0022 → $0.0033) |

**How often the model picks the skill up by itself** (auto arm)

| Model | Discipline | Real work | Small tasks |
|---|---|---|---|
| Haiku 5.5 | 0% | 0% | 0% |
| Sonnet 5.5 | 50% | 0% | 0% |
| Opus 5.5 | 75% | 0% | 0% |
| DeepSeek V4.1 Flash (OpenCode) | 100% | 0% | 0% |

**What the numbers say**

- **Where it is built for, it works on every model.** Discipline tasks gain **+6 to +13 pp** (+10% to +22% relative) with the skill loaded. The cheapest model gains most: DeepSeek V4.1 Flash goes 62% → 75%.
- **Real work: no measurable effect.** All four models solve the three real tasks without the skill — 100% of criteria in every arm — so there is nothing to win on correctness; quality moves within ±5 pp. These tasks turned out too easy to separate the arms; harder ones are the next step.
- **Small tasks are the cost of forcing it.** Loaded on purpose, the skill costs 2–8 pp of polish on trivial tasks. In the *auto* arm it never triggers there (0%), so in normal use small tasks are untouched.
- **Tokens grow ×1.7–1.9, the bill ×1.3–1.5.** The extra steps re-read context that is already cached: on Claude the cache-read share rises from 86–88% to 90–91%, and cache reads bill at a fraction of fresh input. Fresh tokens (uncached input + output) grow only ×1.2–1.4 on Claude; DeepSeek caches less and pays ×1.5.
- **Auto-trigger is the weak spot.** Without being asked, DeepSeek used the skill on 100% of discipline runs, Opus on 75%, Sonnet on 50%, Haiku on 0%.

**How the benchmark changed the skill.** The first v1.1.0 run lost up to 19 pp on real work. The transcripts showed why: agents ran the auto-update script mid-task and pasted SSoT lines and notes about the skill into their answers. Both moved out of the agent's path — updates now run outside tasks, and the deliverable is about the work only. One grader was also fixed: it penalised *adding* tests, which the prompt never forbade (editing or deleting existing tests still fails it).

*Caveats:* small samples (2–5 runs per arm per task); the judge shares a model family with three of the four subjects; real-work tasks hit the ceiling. Per-task numbers with every token class: [`evals/benchmark/RESULTS.md`](evals/benchmark/RESULTS.md).

## Graph replay

<p align="center"><img src="assets/graph-replay.png" alt="Animated replay of a task graph: units, statuses, criteria with evidence, findings and the tool-call timeline" width="900"></p>

When a run is long enough to plan as a graph (FULL mode, or when you ask), the agent records every change to that graph and finishes with a link like `file:///…/.orchestration/vendor-compliance.graph.html`. The page is a single self-contained file:

- **Play, pause, step, drag** through the run; **jump to any graph version** (v1 = first plan, v2… = each replan) or share `#step=N`.
- **Criteria light up** as evidence arrives; delegated units show their worker; removed and skipped units stay visible as dashed boxes.
- **Findings** — automatic checks of the method: DONE only after evidence, a checkpoint after every unit result, skips with a reason, a final SSoT, “complete” only when every required criterion has evidence, briefs and returns kept small.
- With the run transcript (`trace_graph.py analyze --run …`) it also ties every event to the real tool call and splits tokens between the orchestrator and its subagents.

Example: [four models on the same 10-contract review](https://htmlpreview.github.io/?https://github.com/Lexus2016/task-graph-orchestration-skill/blob/main/examples/replay-vendor-contracts.html) — Haiku, Sonnet, Opus and DeepSeek, all 10/10 correct, three of four traces clean.

## What the skill makes the agent do

| Situation | Behaviour the skill asks for |
|---|---|
| Subagent reports “all tests pass” with no CI link | Check the evidence; report the unverified part as unverified |
| Same error twice | Run SSoT, name the shared wrong assumption, test a new cause or escalate |
| Batch of 40 items, 3 fail | 37 DONE with evidence, 3 FAILED with cause, nothing hidden |
| A teammate already did half the work | Inspect the target before writing; mark finished units done; do only the rest |
| Goal reached before the plan ran out | Stop, skip the remaining units as `superseded`, report |
| Session dies mid-run | Resume from the state file; never repeat an external write |
| Tiny edit | Nothing extra — no plan, no ritual |

The benchmark measures the first two rows directly; the others are covered by the skill's rules and the half-finished-migration task, where models already did well without it.

## How it works

| Piece | What it does |
|---|---|
| **Modes** | `DIRECT` (just do it) · `LITE` (compact plan) · `FULL` (unit contracts + resumable state). The smallest mode that fits wins. |
| **Completion contract** | Acceptance criteria marked `required` / `optional`, fixed before work starts. “Done” means every required criterion has evidence. |
| **Units** | Each with input, output, check, dependencies, effect (`read-only` / `reversible` / `consequential`) and a budget. |
| **Failure classes** | Transient, wrong artifact, faulty plan, permission denied, uncertain external write, still pending — each with its own recovery. |
| **Permissions** | Risk, permission and confidence are separate questions. Past success never widens what the agent may do. |
| **Checkpoint** | After every unit result: contract met → stop early; output already exists → `DONE` without running; unit no longer needed → `SKIPPED (superseded)`; plan wrong → replan the affected subgraph. Criteria, not units, are required. |
| **Delegation** | Narrow before reading; delegate only units whose unavoidable reading dwarfs a worker's startup; brief = minimum sufficient context; return = conclusions, not raw material; cheap model for mechanical units. |
| **SSoT** | A deliberate pause plus a structured re-look — on loops, before the final decision, and on request. |
| **Graph trace** | In FULL mode (or on request) the agent appends graph events to `.orchestration/<goal>.trace.jsonl` and ends with a link to the rendered replay page. |
| **State** | JSON state file with single writer, atomic writes, cleanup list, and a run history for recurring workflows. |

### SSoT in one minute

The agent writes 10 characters, picks one by a digit-sum rule, and announces it:

```text
SSoT: Rb7xQ2mT4z (digit-sum 13, pos 3): x.
Re-look: both attempts edited key names, assuming svc-017 uses the default loader.
It uses a custom loader. New unit `loader-shim`; no third retry of the same cause.
```

The characters only create the pause. The re-look does the work: list the attempts, name the assumption they share, then change course.

## Auto-update

The agent never updates itself mid-task. Updates arrive from outside its work:

- `install.sh` schedules a daily background check — `launchd` on macOS, `cron` on Linux.
- The Claude Code plugin checks once per session (`SessionStart` hook).
- Manually: `bash ~/.claude/skills/task-graph-orchestration/scripts/update.sh update`.

The check compares `VERSION` with this repository, downloads the tagged release, validates its name and version, and swaps every local copy atomically. Offline it does nothing. Turn it off with `bash <skill>/scripts/update.sh unschedule`, or install with `TGO_AUTO_UPDATE=0`.

## Works with

| Runtime | How it loads | Notes |
|---|---|---|
| Claude Code | `~/.claude/skills/` or the plugin | Reference adapter in `references/adapters/claude-code.md` |
| Codex | `~/.agents/skills/` | Fallbacks for anything the runtime lacks |
| OpenCode | `~/.config/opencode/skills/` | — |
| Anything else | Paste `SKILL.md` into `AGENTS.md` / system prompt | `references/runtime-adapter.md` maps every capability to a fallback |

## Repository layout

```text
skills/task-graph-orchestration/   the skill: SKILL.md, references/, scripts/ (update.sh, trace_graph.py), assets/trace-viewer.html, VERSION
examples/                          replay pages of real traced runs
evals/                             7 A/B test cases: prompt, expected outcome, graders, input files
evals/harness/                     runners for Claude Code and OpenCode, blind judge, summarizer
evals/benchmark/                   published results: RESULTS.md (per task), summary.json
.claude-plugin/ · hooks/           Claude Code plugin + marketplace manifests · SessionStart update hook
install.sh · PROMPT.md             one-line install · paste-into-agent install
```

## Reproduce the benchmark

```bash
git clone https://github.com/Lexus2016/task-graph-orchestration-skill && cd task-graph-orchestration-skill
MODEL=claude-haiku-5-5 bash evals/harness/ab-run.sh 5 6                       # Claude Code: 7 tasks × 3 arms × 5 runs → .bench/ab/
MODEL=ollama-cloud/deepseek-v4.1-flash:1017 OUT=.bench/ab-ds \
  bash evals/harness/ab-run-opencode.sh 3 4                                    # OpenCode, any model it can reach
AB=.bench/ab python3 -I evals/harness/ab-judge.py                             # blind judge → .bench/ab/results.json
python3 -I evals/harness/summarize.py "Haiku 5.5=.bench/ab/results.json" "DeepSeek=.bench/ab-ds/results.json"
```

`claude plugin eval . --allow-tools Write Edit Bash --scaffold` runs the same cases through Claude Code's built-in runner (its Bash sandbox refuses to start on machines whose `~/.ssh` contains symlinks — the harness above has no such limit). Each case in `evals/` is plain Markdown + YAML, so you can also run it by hand in any agent.

---

<p align="center">If it saved you one fake “done”, a ⭐ helps others find it.</p>

<p align="center">MIT © 2026 Lexus2016</p>
