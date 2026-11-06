<p align="center">
  <img src="assets/social-preview.png" alt="task-graph-orchestration — your agent says done, make it prove it" width="820">
</p>

<h1 align="center">task-graph-orchestration</h1>

<p align="center"><b>Your agent says “done”. This skill makes it prove it.</b></p>

<p align="center">
  <a href="LICENSE"><img alt="MIT" src="https://img.shields.io/badge/license-MIT-blue"></a>
  <img alt="version" src="https://img.shields.io/badge/version-1.4.0-informational">
  <img alt="Claude Code" src="https://img.shields.io/badge/Claude%20Code-skill%20%2B%20plugin-d97757">
  <img alt="Codex" src="https://img.shields.io/badge/Codex-skill-111111">
  <img alt="OpenCode" src="https://img.shields.io/badge/OpenCode-skill-4b5563">
  <a href="#benchmark"><img alt="benchmark" src="https://img.shields.io/badge/final%20report%20accuracy-20%2F20%20vs%205%2F20-brightgreen"></a>
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.uk.md">Українська</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a>
</p>

---

On a bulk import that silently loses rows, agents without the skill gave wrong counts in their final report in 15 of 20 runs; with it, in 0 of 20 (Haiku 5.5, DeepSeek V4.1 Flash). It does not make agents stronger at tasks they already do right, and it costs ×1.3–1.6. [Benchmark ↓](#benchmark)

One drop-in skill for **Claude Code, Codex and OpenCode** that changes how an agent runs anything bigger than a one-liner:

- **Proof, not prose.** A worker saying “tests pass” is a claim. The skill makes the agent open the CI run, the file, the receipt — and label what it could not check as unverified instead of hunting for it elsewhere.
- **Numbers from a command, not by eye.** Every count in the final report is printed by a command that counts exactly that thing; counting lines of output by eye is how reports go wrong.
- **Look at what people will see.** Before “done”, open the result the way a person will — each language, role and state that changed — or check what it renders from. Otherwise the headline says “done except X”.
- **Read the live system before touching it.** Before an email, payment, deploy or deletion: read the record of what already happened, do only the remainder, re-read. Change a running system only through the path it actually runs on, and never leave test records in it.
- **No blind retries.** Two identical failures in a row trigger **SSoT**: stop, name the assumption every attempt shared, change the cause — or escalate.
- **A second look at the moments that matter.** SSoT also fires before committing to a root cause or approach, before the first command that changes something outside the working directory, and before the final answer.
- **Delegate only when it pays.** Subagents only for independent units with heavy reading or long runtimes; a minimal brief (paths, not contents) and a return of about 15 lines. Their answer is a claim too.
- **Small stays small.** A rename stays a rename: no plans, no ceremony.

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

Measured on 2026-11-05/06 with Claude Code 2.1.318 (Haiku 5.5) and OpenCode 2.1.2 (DeepSeek V4.1 Flash). Every run starts in a fresh directory with clean settings: no user `CLAUDE.md` / `AGENTS.md`, no MCP servers, no other skills.

**Method.** Each task runs against a small local mock service (or plain files) that records what the agent really did. Outcomes are checked **by code from that record**; a blind judge (Sonnet 5.5, arm hidden, skill mentions redacted) only checks that the agent's final report matches the record, with the ground-truth numbers supplied. Arms: *no skill* · *v1.2.0* · *v1.3.0*, with the skill installed and the prompt asking for it. v1.4.0, the current version, was checked against v1.3.0 separately (below).

| Task | What is checked | No skill | v1.2.0 | **v1.3.0** |
|---|---|---|---|---|
| Bulk import that silently drops 13 of 40 rows (Haiku + DeepSeek, 10 runs each per arm) | the final report states the right counts | 5 / 20 | 14 / 20 | **20 / 20** |
| Crash after 15 of 40 customer emails, a fresh session finishes the job (Haiku, 5 runs) | every criterion: no duplicate email, everyone notified, decisions right, honest report | 3 / 5 | 2 / 5 | **5 / 5** |
| Human-verification wall that stops activation after 4 of 12 vendors (10 runs) | service state correct and report honest | 10 / 10 | 10 / 10 | 10 / 10 |
| Payment sandbox with 429s, an expiring token and charges that time out after being processed (10 runs) | each invoice charged exactly once and report honest | 9 / 10 | 10 / 10 | 10 / 10 |

**What it costs**, versus no skill, averaged over the three mock-service tasks: Haiku — tokens ×1.25, bill ×1.30, time ×1.23; DeepSeek — tokens ×1.83, bill ×1.61, time ×1.38.

**What this says.** The measurable gain is in the *report*. Agents without the skill got a count wrong in 15 of 20 import runs (mostly the comma-decimal prices: 6, 8, 9, 11, 13 or 14 where the truth was 7) because they counted printed lines by eye. v1.3.0 asks for every number to be printed by a command that counts exactly that, and it was right in all 20. Where agents already behave — the service ended in a correct state in every run of every arm — the skill adds cost and nothing else.

**Correction.** Earlier versions of this README claimed "+6 to +13 percentage points" on discipline tasks. That figure came from a grader that checked whether the answer contained an SSoT line, which only the skill can produce. Graded on outcomes alone, those tasks were solved equally with and without the skill. The claim is withdrawn.

*Caveats:* 5–10 runs per cell and two models (Haiku 5.5, DeepSeek V4.1 Flash); the judge shares a model family with one of them. The v1.3.0 counting rule was written after the import task exposed the problem, so that row is not independent evidence; the refund task was chosen independently and points the same way, but 5 runs are not significant on their own (p = 0.44 against no skill). Two failures of the plain agent seen in a 3-run pilot — a duplicated charge and a stray test record in a live service — did not recur in the 150+ runs that followed. The test cases, mock services and judge are not published in this repository.

**v1.4.0 (current).** Four rules come from a real deploy session in which an agent reviewed a teammate's branch, called it clean and released it — after which every language except English showed message ids instead of text: open what a person will see; read how a running system is actually run before changing it; give a request that arrives mid-work its own criteria; pause (SSoT) before the first command that changes something outside the working directory. Small tasks did not reproduce that failure — without the skill, 20 of 20 runs translated every language — so these rules are checked **for harm only**, not for benefit:

| v1.4.0 vs v1.3.0 (four tasks, Haiku 5.5 + DeepSeek V4.1 Flash, 40 runs per version) | v1.3.0 | v1.4.0 |
|---|---|---|
| Clean result (state correct and report honest) | 39 / 40 | 40 / 40 |
| Cost | — | +8–9 % |
| Time | — | +5–11 % |

## What the skill makes the agent do

| Situation | Behaviour the skill asks for |
|---|---|
| Subagent reports “all tests pass” with no CI link | Open the evidence; report what could not be checked as unverified |
| A report is about to state counts | Print each count with its own command before writing it down |
| Tests are green, but the change has a UI in several languages | Open each changed language and state, or check the catalogs; otherwise “done except X” |
| Same error twice | Run SSoT, name the shared wrong assumption, test a new cause or escalate |
| A crashed batch of emails or payments | Read what was already sent or charged, do only the rest, re-read |
| About to deploy or change a running service | Read how it is actually run now; change it the same way; SSoT before the first command |
| Tiny edit | Nothing extra — no plan, no ritual |

The benchmark measures the counting row directly, and the crash row is the refund task. The UI and live-system rows come from a real deploy session and are checked only for harm; the loop row is a rule the benchmark could not separate from what agents already do.

## How it works

`SKILL.md` is 52 lines in six sections. Each rule answers a failure seen in agent runs.

| Section | What it asks |
|---|---|
| **1. Before acting** | A completion contract of 2–6 checkable criteria, each `required` or `optional`; a mid-work request gets its own. Plan only real dependencies; N similar items are one unit. Look only where the request points. |
| **2. Evidence** | Done = a check run in this session passed. Claims (workers, logs, CI badges, old notes, memory) are not evidence. Numbers come from commands. Irreversible actions: read the record, act on the remainder, re-read. No probe records in live systems. |
| **3. Loops** | A one-line failure ledger; the same error twice or a repeated cause triggers a loop SSoT. Never a third try of the same idea. |
| **4. SSoT** | A deliberate pause plus a re-look from a forced angle (below). |
| **5. Parallel work** | Delegate only when it pays; minimal brief, short return, one owner per mutable output. |
| **6. Final answer** | A silent checklist, then an answer about the work: result, evidence, gaps. No plans, modes or SSoT lines unless asked. |

### SSoT in one minute

The agent writes 10 fresh letters and digits, picks one by a digit-sum rule, and the position sets the angle it must look from:

```text
SSoT: Rb7xQ2mT4z (digit-sum 13, pos 3): x.   angle = 3 mod 5 = reviewer
Re-look: both attempts edited key names, assuming svc-017 uses the default loader.
It uses a custom loader. New unit `loader-shim`; no third retry of the same cause.
```

Angles: 0 user · 1 spec · 2 edge case · 3 reviewer · 4 next agent. If the angle repeats the previous one in the same task, the agent takes the next. It fires on a loop, before a commitment the rest of the work depends on, before marking done a unit no check covers, before the first command of a batch that changes something outside the working directory, before the final answer, and when you write “SSoT”. Its lines stay out of the final answer unless you ask.

The characters only create the pause; the re-look does the work. **Honest note:** in 80 benchmark runs that loaded the skill on request, an SSoT line appeared only twice — agents often skip it.

## Long, resumable or recurring work

When work must survive the session — overnight runs, multi-session batches, recurring jobs — the skill points to `scripts/tgo.py`, a small state machine on disk (plan, start, done with a check, failure ledger, final), and `references/full-mode.md` for checkpoints, resume and monitoring. An optional graph-trace viewer (`scripts/trace_graph.py`, `assets/trace-viewer.html`, `references/trace.md`) renders a recorded run as an animated graph; the core skill does not turn it on.

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
skills/task-graph-orchestration/   the skill: SKILL.md, references/, scripts/ (update.sh, tgo.py, trace_graph.py), assets/trace-viewer.html (optional), VERSION
tests/                             unit tests for the helper scripts
.claude-plugin/ · hooks/           Claude Code plugin + marketplace manifests · SessionStart update hook
install.sh · PROMPT.md             one-line install · paste-into-agent install
```

## About the benchmark

The test cases, mock services and the blind judge are kept outside this repository; it ships only the skill and these READMEs. The **Benchmark** section above describes the method, the results, the cost and the limits.

---

<p align="center">If it saved you one fake “done”, a ⭐ helps others find it.</p>

<p align="center">MIT © 2026 Lexus2016</p>
