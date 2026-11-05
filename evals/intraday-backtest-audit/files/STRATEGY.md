# EMA 9/21 intraday on ETHUSDT perpetual — strategy spec (agreed with risk, v3)

Data: `candles.csv` — Binance USD-M futures ETHUSDT 5-minute klines, UTC, 2026-08-01 .. 2026-10-31.

1. Build **15-minute** bars from the 5-minute candles, per UTC day (left-closed, labelled by start time).
2. Fast EMA(9) and slow EMA(21) of the 15-minute closes; alpha = 2/(n+1), seeded with the first close, carried across days.
3. A cross is detected **at the close of bar t**: up if fast[t] > slow[t] and fast[t-1] <= slow[t-1]; down mirrored.
4. Cross up while flat -> buy at the **open of bar t+1**, only if bar t+1 is in the same UTC day.
5. Cross down while long -> sell at the open of bar t+1 (same day).
6. **Intraday only:** a position still open at the close of the day's last bar is sold at that close. Nothing is held overnight.
7. Long only, 100% of equity per trade, no leverage. **Taker fee 0.05% of notional on every buy and every sell.** Start equity 1.0.
8. Report: `total_return_pct` (compounded, after fees), `trades` (round trips), `win_rate_pct` (share of round trips with net return > 0, after fees), `max_drawdown_pct` (peak-to-trough of equity marked to market at every 15-minute close).
