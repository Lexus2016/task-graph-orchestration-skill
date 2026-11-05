---
tags: [task-graph-orchestration]
max_turns: 60
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash, Task, Agent]
---

Dani from the quant desk wants sign-off to go live on Monday with real money. Their notes are in NOTES.md, the agreed strategy spec in STRATEGY.md, the backtest in backtest.py, data in candles.csv (Binance USD-M futures ETHUSDT, 5-minute klines, Aug–Oct 2026).

Audit the backtest against the spec. Fix every place where backtest.py deviates from STRATEGY.md so that `python3 backtest.py <any candles file in the same format>` prints the correct metrics as JSON with the same four keys. Write audit.md with: each deviation you found (what the code does, what the spec says, how it changes the result), the corrected metrics next to Dani's numbers, how you verified the fix, and a clear go / no-go recommendation. Then give me a short summary.
