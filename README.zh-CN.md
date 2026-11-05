<p align="center"><img src="assets/social-preview.png" alt="task-graph-orchestration" width="820"></p>

<h1 align="center">task-graph-orchestration</h1>

<p align="center"><b>你的 Agent 说“完成了”。这个 Skill 让它拿出证据。</b></p>

<p align="center"><a href="README.md">English</a> · <a href="README.uk.md">Українська</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a></p>

---

在 Agent 最容易偷工减料的任务上，盲评质量分提升 **+1.75（Sonnet 5.5）**、**+1.0（Opus 5.5）**、**+0.6（Haiku 5.5）**（满分 10），小任务不受影响。

一个适用于 **Claude Code、Codex 和 OpenCode** 的 Skill，改变 Agent 处理多步骤任务的方式：

- **证据，而不是说法。** 子 Agent 说“测试全部通过”只是一个声明。Skill 要求 Agent 去核对 CI 运行、文件或回执。
- **不再盲目重试。** 连续两次相同的失败会触发 **SSoT**：停下来，找出所有尝试共同的错误假设，换一个原因去验证，或者上报。
- **交付前的第二次审视。** 在最终报告前，Agent 以“没写过这份结果的评审者”的视角重读一遍。
- **小任务保持简单。** 改个名字就只是改名字，没有计划，没有仪式。

## 安装

**直接粘贴给你的 Agent：**

```text
Install the agent skill from https://github.com/Lexus2016/task-graph-orchestration-skill —
run its install.sh, show me the INSTALLED line, and tell me to restart you.
```

**终端一行命令：**

```bash
curl -fsSL https://raw.githubusercontent.com/Lexus2016/task-graph-orchestration-skill/main/install.sh | bash
```

**Claude Code 插件：** `/plugin marketplace add Lexus2016/task-graph-orchestration-skill`，然后 `/plugin install task-graph-orchestration@task-graph-orchestration`。

## 基准测试

测试日期 2026-11-05：Claude Code 2.1.318，`claude -p` 无头模式，干净配置，每次运行使用独立目录。目标任务：同一个修复连续失败两次；基于三个子 Agent 声明（其中一个没有证据）撰写最终报告。对照任务：检查四个配置文件；重命名一个函数。质量 1–10 分由不知道分组的盲评裁判（Sonnet 5.5）给出。

**目标任务质量**

| 模型 | 每组运行次数 | 不使用 Skill | 使用 Skill（已加载） | Δ | 使用 Skill（自动触发） | Δ |
|---|---|---|---|---|---|---|
| Haiku 5.5 | 5 | 5.90 | 6.50 | **+0.60** | 5.90 | +0.00 |
| Sonnet 5.5 | 2 | 5.75 | 7.50 | **+1.75** | 6.25 | +0.50 |
| Opus 5.5 | 2 | 5.75 | 6.75 | **+1.00** | 8.00 | +2.25 |

**代价**（目标任务，不使用 → 已加载）

| 模型 | 耗时 | 轮次 | 工具调用 | Token | 成本 |
|---|---|---|---|---|---|
| Haiku 5.5 | 22.9 → 68.3 s (×3.0) | 3.0 → 7.4 | 2.0 → 5.4 | 50k → 150k (×3.0) | $0.0024 → $0.0049 (×2.0) |
| Sonnet 5.5 | 11.3 → 23.7 s (×2.1) | 2.0 → 3.8 | 1.0 → 1.8 | 29k → 62k (×2.1) | $0.0314 → $0.0378 (×1.2) |
| Opus 5.5 | 11.9 → 20.2 s (×1.7) | 1.5 → 4.0 | 0.5 → 2.0 | 29k → 69k (×2.4) | $0.0572 → $0.0864 (×1.5) |

**小任务保持简单**（对照任务，质量 1–10）

| 模型 | 不使用 Skill | 使用 Skill（已加载） | 使用 Skill（自动触发） |
|---|---|---|---|
| Haiku 5.5 | 9.00 | 8.70 | 9.00 |
| Sonnet 5.5 | 8.25 | 8.50 | 8.50 |
| Opus 5.5 | 9.00 | 9.00 | 8.75 |

- 加载后所有模型都有提升：Haiku **+0.6**、Opus **+1.0**、Sonnet **+1.75**。最弱的模型提升最少。
- Opus 在 4/4 个目标运行中主动调用了 Skill，在对照运行中 0/4，得分 **+2.25**，为全表最佳。
- 代价：耗时 ×1.7–3、Token ×2–3，仅在 Skill 触发时产生。小任务质量变化在 ±0.3 以内。

详细数据与说明：[README.md](README.md#benchmark)、[`evals/benchmark/RESULTS.md`](evals/benchmark/RESULTS.md)。

## 自动更新

每次完成计划模式（LITE 或 FULL）运行后，Skill 会运行 `bash scripts/update.sh check`：每天最多检查一次本仓库的 `VERSION`，下载并校验带标签的发布版本，然后更新所有本地副本，下次运行生效。离线时不会阻塞任务；设置 `TGO_AUTO_UPDATE=0` 可关闭。

完整文档见 [README.md](README.md)。MIT © 2026 Lexus2016。如果它帮你识破了一次虚假的“完成”，欢迎点个 ⭐。
