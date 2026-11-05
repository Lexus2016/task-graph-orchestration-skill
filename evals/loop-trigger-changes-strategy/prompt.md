---
tags: [task-graph-orchestration]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

im migrating our 12 services to the new config loader in parallel, 11 went fine. svc-billing failed twice now, both times with `KeyError: 'db.url'` — first attempt i renamed the keys to v2 names, second attempt i renamed them again with the nested format from the docs. same error. what do we do next? dont just tell me to retry
