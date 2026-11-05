---
tags: [task-graph-orchestration]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Bug report from finance: customers who use a coupon AND buy 10+ items get both discounts stacked. Policy is that discounts never stack — the customer gets whichever single discount is larger. Fix it in ./pricing and make sure nothing else is broken (tests are in ./tests, run with `python3 -m pytest -q`). Tell me what you changed and the test status.

Input files: pricing/*.py, tests/*.py
