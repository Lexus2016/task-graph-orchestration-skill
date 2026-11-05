# Paste this into your agent

> Install the agent skill from https://github.com/Lexus2016/task-graph-orchestration-skill.
> Run `curl -fsSL https://raw.githubusercontent.com/Lexus2016/task-graph-orchestration-skill/main/install.sh | bash`,
> show me the `INSTALLED` line it prints, and tell me to restart you so the skill loads.

Works in Claude Code, Codex and OpenCode. The script copies `skills/task-graph-orchestration/` into every local
agent skills folder it finds (`~/.claude/skills`, `~/.agents/skills`, `~/.config/opencode/skills`) and nothing else.
