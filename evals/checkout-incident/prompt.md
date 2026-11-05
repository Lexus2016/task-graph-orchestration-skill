---
tags: [task-graph-orchestration]
max_turns: 60
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash, Task, Agent]
---

Checkout was down for about 20 minutes on 2026-10-21 starting around 14:03 UTC. Logs are in ./logs (including deploys.log), payments config in ./config, the payments client in ./services/payments, tests in ./tests (`python3 -m pytest -q`).

Find the root cause and anything that made it worse, back every claim with log lines and timestamps, and fix whatever is still broken in the repo so this can't recur. Write incident.md with: timeline, root cause, contributing factors, what you changed, and how you verified it. Then give me a short summary.
