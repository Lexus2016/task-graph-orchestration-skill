<p align="center">
  <img src="assets/social-preview.png" alt="task-graph-orchestration — your agent says done, make it prove it" width="820">
</p>

<h1 align="center">task-graph-orchestration</h1>

<p align="center"><b>Your agent says “done”. This skill makes it prove it.</b></p>

<p align="center">
  <a href="LICENSE"><img alt="MIT" src="https://img.shields.io/badge/license-MIT-blue"></a>
  <img alt="version" src="https://img.shields.io/badge/version-1.0.1-informational">
  <img alt="Claude Code" src="https://img.shields.io/badge/Claude%20Code-skill%20%2B%20plugin-d97757">
  <img alt="Codex" src="https://img.shields.io/badge/Codex-skill-111111">
  <img alt="OpenCode" src="https://img.shields.io/badge/OpenCode-skill-4b5563">
  <a href="#benchmark"><img alt="benchmark" src="https://img.shields.io/badge/benchmark-%2B1.0..1.75%20quality-brightgreen"></a>
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.uk.md">Українська</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a>
</p>

---

On tasks where agents usually cut corners it raises a blind-judged quality score by **+1.75 (Sonnet 5.5)**, **+1.0 (Opus 5.5)** and **+0.6 (Haiku 5.5)** out of 10 — and leaves small tasks alone. [Benchmark ↓](#benchmark)

One drop-in skill for **Claude Code, Codex and OpenCode** that changes how an agent runs anything bigger than a one-liner:

- **Proof, not prose.** A worker saying “tests pass” is a claim. The skill makes the agent check the CI run, the file, the receipt.
- **No blind retries.** Two identical failures in a row trigger **SSoT**: stop, name the assumption every attempt shared, change the cause — or escalate.
- **A second look before “done”.** Before the final report the agent re-reads its own result as a reviewer who didn’t write it.
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

Measured on 2026-11-05 with Claude Code 2.1.318, headless `claude -p`, clean settings (no user `CLAUDE.md`, no MCP servers), one fresh working directory per run.

- **Target tasks**, where the skill should matter: a fix that failed twice with the same error; a final status report built on three subagent claims, one of them without evidence.
- **Control tasks**, where it should stay out of the way: checking four configs with two broken ones; renaming one function and running the tests.
- **Arms:** *without* (no skill) · *loaded* (skill installed and the prompt says to use it) · *auto* (skill installed, the model decides).
- **Scoring:** a blind judge (Sonnet 5.5, never told the arm, skill mentions redacted) gives quality 1–10 and grades each criterion; files, renames and SSoT arithmetic are checked by code.

**Quality on target tasks** (1–10, higher is better)

| Model | Runs per arm | Without skill | With skill (loaded) | Δ | With skill (auto-trigger) | Δ |
|---|---|---|---|---|---|---|
| Haiku 5.5 | 5 | 5.90 | 6.50 | **+0.60** | 5.90 | +0.00 |
| Sonnet 5.5 | 2 | 5.75 | 7.50 | **+1.75** | 6.25 | +0.50 |
| Opus 5.5 | 2 | 5.75 | 6.75 | **+1.00** | 8.00 | +2.25 |

**What it costs** on target tasks, *without → loaded*

| Model | Time | Turns | Tool calls | Tokens | Cost |
|---|---|---|---|---|---|
| Haiku 5.5 | 22.9 → 68.3 s (×3.0) | 3.0 → 7.4 | 2.0 → 5.4 | 50k → 150k (×3.0) | $0.0024 → $0.0049 (×2.0) |
| Sonnet 5.5 | 11.3 → 23.7 s (×2.1) | 2.0 → 3.8 | 1.0 → 1.8 | 29k → 62k (×2.1) | $0.0314 → $0.0378 (×1.2) |
| Opus 5.5 | 11.9 → 20.2 s (×1.7) | 1.5 → 4.0 | 0.5 → 2.0 | 29k → 69k (×2.4) | $0.0572 → $0.0864 (×1.5) |

Dollar cost swings with prompt-cache warmth; tokens and turns are the steadier signal.

**Small tasks stay small** (control tasks, quality 1–10)

| Model | Without skill | With skill (loaded) | With skill (auto-trigger) |
|---|---|---|---|
| Haiku 5.5 | 9.00 | 8.70 | 9.00 |
| Sonnet 5.5 | 8.25 | 8.50 | 8.50 |
| Opus 5.5 | 9.00 | 9.00 | 8.75 |

**What the numbers say**

- Loaded, the skill improves every model: **+0.6** Haiku, **+1.0** Opus, **+1.75** Sonnet. We expected the weakest model to gain most; it gains least — Haiku follows the procedure (2.7× tool calls) but turns the extra steps into little extra quality.
- Auto-trigger depends on the model. Opus picked the skill up on 4/4 target runs and 0/4 control runs and scored **+2.25** — the best result in the table. Sonnet triggered on 2/4, Haiku on 5/10 with no gain.
- The price is 1.7–3× time and 2–3× tokens, paid only where the skill triggers. On control tasks quality stays within ±0.3 of the baseline.
- The benchmark changed the skill before release: round one showed **0/36** auto-triggers (fixed in the description) and ceremony on small tasks (fixed with an early “small task? stop here” exit — control quality with the skill loaded rose 7.7 → 8.7 on Haiku and 8.0 → 9.0 on Opus).

*Caveats:* four tasks; 5 runs per arm per task on Haiku, 2 on Sonnet and Opus; the judge shares a model family with two of the subjects. Per-task numbers: [`evals/benchmark/RESULTS.md`](evals/benchmark/RESULTS.md). Raw summary: [`evals/benchmark/summary.json`](evals/benchmark/summary.json).

## What changes

| Situation | Agent without the skill | Agent with the skill |
|---|---|---|
| Subagent reports “all tests pass” with no CI link | Repeats it in the final report | Checks the evidence, reports the unverified part as unverified |
| Same error twice | Tries a third variation of the same fix | Runs SSoT, names the shared wrong assumption, tests a new cause |
| Batch of 40 items, 3 fail | “Done!” | 37 DONE with evidence, 3 FAILED with cause, nothing hidden |
| Tiny edit | Fine | Exactly the same — no plan, no ritual |
| Session dies mid-run | Starts over | Resumes from the state file; never repeats an external write |

## How it works

| Piece | What it does |
|---|---|
| **Modes** | `DIRECT` (just do it) · `LITE` (compact plan) · `FULL` (unit contracts + resumable state). The smallest mode that fits wins. |
| **Completion contract** | Acceptance criteria marked `required` / `optional`, fixed before work starts. “Done” means every required criterion has evidence. |
| **Units** | Each with input, output, check, dependencies, effect (`read-only` / `reversible` / `consequential`) and a budget. |
| **Failure classes** | Transient, wrong artifact, faulty plan, permission denied, uncertain external write, still pending — each with its own recovery. |
| **Permissions** | Risk, permission and confidence are separate questions. Past success never widens what the agent may do. |
| **SSoT** | A deliberate pause plus a structured re-look — on loops, before the final decision, and on request. |
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

After a planned (LITE or FULL) run the skill runs `bash scripts/update.sh check`, off the critical path: at most once a day it compares its `VERSION` with this repository, downloads the tagged release, validates it, and refreshes every local copy for the next run. It never blocks work and exits 0 when offline. Opt out with `TGO_AUTO_UPDATE=0`.

## Works with

| Runtime | How it loads | Notes |
|---|---|---|
| Claude Code | `~/.claude/skills/` or the plugin | Reference adapter in `references/adapters/claude-code.md` |
| Codex | `~/.agents/skills/` | Fallbacks for anything the runtime lacks |
| OpenCode | `~/.config/opencode/skills/` | — |
| Anything else | Paste `SKILL.md` into `AGENTS.md` / system prompt | `references/runtime-adapter.md` maps every capability to a fallback |

## Repository layout

```text
skills/task-graph-orchestration/   the skill (SKILL.md, references/, scripts/update.sh, VERSION)
evals/                             A/B test cases: prompt, expected outcome, graders
.claude-plugin/                    Claude Code plugin + marketplace manifests
install.sh · PROMPT.md             one-line install · paste-into-agent install
```

## Reproduce the benchmark

```bash
git clone https://github.com/Lexus2016/task-graph-orchestration-skill && cd task-graph-orchestration-skill
MODEL=claude-haiku-5-5 bash evals/harness/ab-run.sh 5 6                 # 4 tasks × 3 arms × 5 runs → .bench/ab/
AB=.bench/ab python3 -I evals/harness/ab-judge.py                       # blind judge → .bench/ab/results.json
python3 -I evals/harness/summarize.py "Haiku 5.5=.bench/ab/results.json"  # the tables above
```

`claude plugin eval . --allow-tools Write Edit Bash --scaffold` runs the same cases through Claude Code's built-in runner (its Bash sandbox refuses to start on machines whose `~/.ssh` contains symlinks — the harness above has no such limit). Each case in `evals/` is plain Markdown + YAML, so you can also run it by hand in any agent.

---

<p align="center">If it saved you one fake “done”, a ⭐ helps others find it.</p>

<p align="center">MIT © 2026 Lexus2016</p>
