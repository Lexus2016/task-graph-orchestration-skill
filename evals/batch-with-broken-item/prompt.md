---
tags: [task-graph-orchestration]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

we're about to ship these service configs in ./configs. check every one of them: each must be valid JSON with a string `name` and an integer `port` between 1 and 65535. write the results to report.md (one line per file, ok or what's wrong) and tell me if we're good to ship

Input files: configs/a.json, configs/b.json, configs/c.json, configs/d.json
