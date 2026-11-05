---
tags: [task-graph-orchestration]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

I'm sizing a job queue against the Quillstream API. Using only the files in ./sources, what are the current per-minute rate limits for the free and the paid plan? Some of these sources disagree. Write answer.md with the two numbers, which file each one comes from, and which sources you discarded and why.

Input files: sources/*.md
