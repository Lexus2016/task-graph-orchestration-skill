# Runtime adapter

Read this at the start of a LITE or FULL run. The skill speaks in capabilities; this file says what each one is, how to tell whether your runtime has it, and what to do when it does not. If `adapters/<runtime>.md` exists for your runtime, read it too — it names the concrete tools.

## Capability map

| Capability | Look for | Fallback when missing |
|---|---|---|
| **Workers** (separate contexts) | a subagent / delegate / spawn tool, a CLI you can start as a child process, or a second agent session | Run units yourself, one at a time. Keep contexts apart on purpose: write each BRIEF to a file, work only from it, write the RETURN block to a file, and verify from the artifacts, not from memory of doing the work. Concurrency = 1. |
| **Parallelism** | a way to start several workers in one step | Sequential execution in dependency order; independent units first if any of them can fail fast. |
| **Isolated code edits** | worktree support in the runtime, or a shell with `git worktree add` | Disjoint file sets per unit, or strictly sequential edits with one owner. |
| **Task store** | a built-in todo / task / plan tool that survives the session | The state file (`state-schema.md`). For LITE, keep the compact plan in the reply. |
| **Wait for a local process** | background execution that notifies on exit | Run in the foreground if short; otherwise start it detached, record its PID and log path as a pending operation, and check them at each resume. |
| **Wait for external state** (CI, deploy, queue) | a scheduler, wake-up, cron or loop facility | Record `pending_op.id` and `next_check` in the state file, report the unit as WAITING, and tell the user when to resume. Never busy-poll in a tight loop. |
| **Ask the user mid-run** | an interactive question tool or a chat turn | Headless: units that need the answer become BLOCKED with the question; finish unaffected work; lead the final report with the question. |
| **Permission prompts** | the runtime asks the user before some actions | A denied or refused action is a permission denial: stop it and do not route around it. |
| **Durable memory** | a memory / notes store | The state file plus the final report. Never write secrets into either. |
| **Cleanup handles** | stop / cancel / kill for tasks, schedules, worktrees, servers | Keep a `started` list in the state file (PIDs, schedule IDs, worktree paths, ports) and stop each item at the end, except those serving a live user commitment. |

## Worker caps

Workers = min(the runtime's or user's configured cap, independent READY units, what you can integrate and verify). If no cap is configured, start with 2 and raise only while integration keeps up.

## Installing the skill

The folder follows the common `SKILL.md` layout (YAML frontmatter with `name` and `description`, Markdown body, `references/`). Install it where your runtime discovers skills — for example `~/.claude/skills/task-graph-orchestration/` for Claude Code; several runtimes (Codex, Copilot CLI, Gemini CLI) also read `~/.agents/skills/`. Check your runtime's documentation for its path.

**Runtimes without skill loading:** put the body of `SKILL.md` into the agent's standing instructions (`AGENTS.md`, a system prompt, a rules file), and keep the `references/` folder next to it so the agent can open the files by path when the body tells it to.

## Writing an adapter for a new runtime

Copy `adapters/claude-code.md`, keep its table's left column, and fill in the right column with that runtime's actual tools. List only tools you have confirmed exist; leave a row on its fallback when unsure.
