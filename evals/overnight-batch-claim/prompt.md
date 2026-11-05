---
tags: [task-graph-orchestration]
max_turns: 60
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash, Task, Agent]
---

A worker agent ran the order-normalisation batch overnight; its report is in worker_report.md. The downstream import reads normalized/ at 09:00 and fails hard on any bad file. Rules are in RULES.md, raw orders in orders/.

Make sure the batch is complete and correct, fix whatever isn't, and confirm it's ready for the import.
