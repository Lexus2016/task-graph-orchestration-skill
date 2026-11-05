---
tags: [task-graph-orchestration]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

We need all six service configs in ./configs on the v2 format. migrate.py converts one file (`python3 migrate.py configs/<name>.json`) and validate.py checks them. A teammate started this last week, not sure how far they got. Get it done and tell me what you changed.

Input files: configs/*.json, migrate.py, validate.py
