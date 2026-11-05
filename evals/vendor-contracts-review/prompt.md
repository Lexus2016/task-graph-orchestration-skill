---
tags: [task-graph-orchestration]
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash, Task, Agent]
---

Legal wants a compliance pass on our 10 vendor contracts in ./contracts against ./policy.md before the quarterly review. Write report.md with exactly one line per contract: `<file name>: OK` or `<file name>: VIOLATION — <rule(s) broken and the clause>`. Signed amendments override the main text. Then tell me which vendors we need to renegotiate with.

Input files: contracts/*.md, policy.md
