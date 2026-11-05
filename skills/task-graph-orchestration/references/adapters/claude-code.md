# Adapter: Claude Code

Concrete tools for the capabilities in `../runtime-adapter.md` — same rows, same names. Tool availability varies by session: check the tool list instead of assuming one exists, and use the fallback from `../runtime-adapter.md` when a tool is missing.

| Capability | Claude Code tool |
|---|---|
| **Workers** | `Agent` tool with the BRIEF as its prompt. A subagent sees only its brief: include task-local context, owned outputs, user restrictions and the RETURN format. |
| **Parallelism** | Several `Agent` calls in one message. A deterministic multi-agent pipeline: `Workflow` tool, only when the user explicitly opted into multi-agent orchestration. Cap = the lower of the agent caps in `settings.json` and the session's workflow size guideline. |
| **Isolated code edits** | `Agent` with `isolation: "worktree"`, or `EnterWorktree` / `ExitWorktree`. |
| **Task store** | The session's task / todo tool if listed; otherwise the state file. |
| **Wait for a local process** | `Bash` with `run_in_background`, or `Monitor` — you are notified on exit; don't poll. |
| **Wait for external state** | `ScheduleWakeup` in `/loop` mode, or `CronCreate`, with a delay matched to how fast that state changes. |
| **Ask the user mid-run** | `AskUserQuestion`, or a plain question in the reply. Headless runs (`claude -p`): use the BLOCKED fallback. |
| **Permission prompts** | A denied tool call is the user declining it: don't retry it verbatim and don't route around it. |
| **Durable memory** | A memory MCP server if one is configured; otherwise the state file and the final report. |
| **Cleanup handles** | `TaskStop` for background tasks, `CronDelete` for scheduled jobs, `ScheduleWakeup` with `stop: true` for loops, `ExitWorktree` for worktrees you created; kill servers you started. |

A subagent's final report is a claim — check the artifacts it names before marking its unit DONE.
