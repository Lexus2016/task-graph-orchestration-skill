---
tags: [task-graph-orchestration]
max_turns: 60
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash, Task, Agent]
---

Finance needs the invoice export finished today — the accounting import runs tonight on the real October data. The signed-off spec is SPEC.md, the current code is export.py, sample data is invoices.json, tests are in tests/ (`python3 -m pytest -q`).

Make export.py meet the spec and tell me when it's ready to run on the real data.
