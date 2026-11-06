<p align="center"><img src="assets/social-preview.png" alt="task-graph-orchestration" width="820"></p>

<h1 align="center">task-graph-orchestration</h1>

<p align="center"><b>你的 Agent 说“完成了”。这个 Skill 让它拿出证据。</b></p>

<p align="center"><a href="README.md">English</a> · <a href="README.uk.md">Українська</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a></p>

---

在一次悄悄丢行的批量导入中，不使用 Skill 的 Agent 在最终报告里给出错误数字的有 15/20 次；使用后为 0/20（Haiku 5.5、DeepSeek V4.1 Flash）。它不会让 Agent 在本来就做得对的任务上变强，成本为 ×1.3–1.6。[基准测试 ↓](#基准测试)

一个适用于 **Claude Code、Codex 和 OpenCode** 的 Skill，改变 Agent 处理多步骤任务的方式：

- **证据，而不是说法。** 子 Agent 说“测试全部通过”只是一个声明。Skill 要求 Agent 去核对 CI 运行、文件或回执。
- **数字来自命令，而不是目测。** 报告里的每个数字都必须由一条专门统计该项的命令打印出来；凭眼睛数输出的行，正是报告出错的原因。
- **不再盲目重试。** 连续两次相同的失败会触发 **SSoT**：停下来，找出所有尝试共同的错误假设，换一个原因去验证，或者上报。
- **交付前的第二次审视。** 在最终报告前，Agent 以“没写过这份结果的评审者”的视角重读一遍。
- **提前完成，跳过已完成的部分。** 每一步之后 Agent 会检查整个计划：目标已达成就停止；工作已完成就直接标记为完成而不重做；计划有误就只重新规划出错的部分。
- **看到过程，而不只是结果。** 长任务结束时附上任务图动画回放的链接：每次计划、重新规划、跳过、检查点和 SSoT，以及对方法执行情况的自动检查。
- **只在值得时才委派。** 先缩小范围再阅读；给子 Agent 最少的上下文（路径而非内容），并要求简短的结果。
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

测试日期 2026-11-05/06：Haiku 5.5 使用 Claude Code 2.1.318，DeepSeek V4.1 Flash 使用 OpenCode 2.1.2。每次运行都在干净目录中，不加载用户的 `CLAUDE.md`/`AGENTS.md`、MCP 或其他 Skill。

**方法。** 每个任务都对接一个小型本地模拟服务（或普通文件），由它记录 Agent 实际做了什么。结果由**代码根据该记录**检查；盲评裁判（Sonnet 5.5，隐藏分组，屏蔽 Skill 相关提及）只核对 Agent 的最终报告是否与记录一致，并提供标准答案中的数字。分组：*不使用* · *v1.2.0* · *v1.3.0*（本仓库的版本），均已安装 Skill 并在提示中要求使用。

| 任务 | 检查内容 | 不使用 | v1.2.0 | **v1.3.0** |
|---|---|---|---|---|
| 批量导入悄悄丢掉 40 行中的 13 行（Haiku + DeepSeek，每组各 10 次运行） | 最终报告中的数字正确 | 5 / 20 | 14 / 20 | **20 / 20** |
| 发出 40 封客户邮件中的 15 封后崩溃，新会话接手完成（Haiku，5 次运行） | 全部标准：无重复邮件、所有人都通知到、决定正确、报告如实 | 3 / 5 | 2 / 5 | **5 / 5** |
| 人工验证门槛使激活在 12 家供应商中的 4 家后停止（10 次运行） | 服务状态正确且报告如实 | 10 / 10 | 10 / 10 | 10 / 10 |
| 支付沙箱：429、令牌过期、已处理却超时的扣款（10 次运行） | 每张发票恰好扣款一次且报告如实 | 9 / 10 | 10 / 10 | 10 / 10 |

**成本**（相对不使用 Skill，三个模拟服务任务的平均值）：Haiku — Token ×1.25，账单 ×1.30，时间 ×1.23；DeepSeek — Token ×1.83，账单 ×1.61，时间 ×1.38。

**这说明什么。** 可测量的收益在*报告*上。不使用 Skill 的 Agent 在 20 次导入运行中有 15 次数字出错（主要是逗号小数的价格：真实值为 7，却报告成 6、8、9、11、13 或 14），因为它们是凭眼睛数输出的行。v1.3.0 要求每个数字都由专门统计该项的命令打印出来，20 次全部正确。在 Agent 本来就表现良好的地方（所有分组的每次运行中，服务最终状态都正确），Skill 只增加成本。

**更正。** 本 README 早期版本曾声称在纪律类任务上提升“+6 到 +13 个百分点”。该数字来自一条检查答案中是否含有 SSoT 行的评分项，而只有使用 Skill 的一组才可能产生这一行。仅按结果评分，这些任务在使用与不使用 Skill 时完成情况相同。该说法已撤回。

*说明：* 每个单元 5–10 次运行，仅两个模型（Haiku 5.5、DeepSeek V4.1 Flash）；裁判与其中一个模型同属一个系列。v1.3.0 的计数规则是在导入任务暴露问题之后写的，因此该行不是独立证据；退款任务是独立选取的，方向一致，但 5 次运行本身不显著（与不使用相比 p = 0.44）。在 3 次运行的试点中看到的普通 Agent 的两次失败（重复扣款，以及在线上服务中留下多余的测试记录）在随后 150 多次运行中没有再出现。测试用例、模拟服务和裁判不在本仓库中发布。

**v1.4.0。** 新增的四条规则来自一次真实的部署会话：Agent 审查了同事的分支，认为没有问题并发布，结果除英语外的所有语言都显示消息 ID 而不是文字。现在要求：在说“完成”之前，按用户看到的方式打开结果（每个改动过的语言、角色和状态），或检查它的渲染来源；修改运行中的系统之前，先读取它当前实际的运行方式；工作中途到来的新请求要有自己的验收标准；在第一条改动工作目录之外内容的命令之前做一次 SSoT。小任务无法复现这个故障（不使用 Skill 时 20 次运行全部翻译了所有语言），因此这些规则只做了无害性检查：在四个任务上与 v1.3.0 对比，Haiku 5.5 和 DeepSeek V4.1 Flash 每个版本各 40 次运行，完全正确 40/40 对 39/40，成本 +8–9%，耗时 +5–11%。在这 80 次按要求加载 Skill 的运行中，SSoT 行只出现了两次。

## 自动更新

Agent 不会在任务中途自我更新。`install.sh` 会安排每日后台检查（macOS 用 `launchd`，Linux 用 `cron`），Claude Code 插件在每个会话开始时检查一次（`SessionStart` 钩子）。检查会比对本仓库的 `VERSION`，下载并校验带标签的发布版本，然后原子替换所有本地副本。关闭：`bash <skill>/scripts/update.sh unschedule`，或安装时设置 `TGO_AUTO_UPDATE=0`。

完整文档见 [README.md](README.md)。MIT © 2026 Lexus2016。如果它帮你识破了一次虚假的“完成”，欢迎点个 ⭐。
