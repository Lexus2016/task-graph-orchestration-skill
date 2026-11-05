"""Reference implementation of the intraday-backtest eval strategy (used by the generator and the judge).

Spec (mirrors evals/intraday-backtest-audit/files/STRATEGY.md):
- Resample 5-minute candles to 15-minute bars, left-closed, labelled by start time, within each UTC day.
- EMA(9) and EMA(21) of 15-minute closes, alpha = 2/(n+1), seeded with the first close, computed across days.
- At the close of bar t (t >= 1): cross up if fast[t] > slow[t] and fast[t-1] <= slow[t-1]; cross down mirrored.
- Cross up while flat -> buy at the open of bar t+1, only if bar t+1 is on the same UTC day.
- Cross down while long -> sell at the open of bar t+1 (same day), else the end-of-day rule applies.
- End of day: a position still open at the close of the day's last bar is sold at that close. No overnight risk.
- Long only, 100% of equity, fee 0.05% of notional on every buy and every sell. Start equity 1.0.
- Metrics: total_return_pct (compounded, after fees), trades (round trips), win_rate_pct (net return > 0),
  max_drawdown_pct (peak-to-trough of equity marked to market at every bar close)."""
import csv
from datetime import datetime

FEE = 0.0005
BAR_MIN = 15


def load(path):
    rows = []
    with open(path) as fh:
        for r in csv.DictReader(fh):
            rows.append((r["ts"], float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"])))
    return rows


def resample(rows):
    bars = []
    for ts, o, h, l, c in rows:
        t = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
        key = (t.date(), t.hour, t.minute // BAR_MIN)
        if bars and bars[-1]["key"] == key:
            b = bars[-1]; b["high"] = max(b["high"], h); b["low"] = min(b["low"], l); b["close"] = c
        else:
            bars.append({"key": key, "day": t.date(), "open": o, "high": h, "low": l, "close": c})
    return bars


def ema(values, n):
    a, out = 2 / (n + 1), []
    for v in values:
        out.append(v if not out else a * v + (1 - a) * out[-1])
    return out


def backtest(bars):
    closes = [b["close"] for b in bars]
    fast, slow = ema(closes, 9), ema(closes, 21)
    eq, peak, mdd = 1.0, 1.0, 0.0
    pos_entry, pos_eq = None, None
    trades, wins = 0, 0
    for t, b in enumerate(bars):
        last_of_day = t + 1 >= len(bars) or bars[t + 1]["day"] != b["day"]
        mtm = pos_eq * b["close"] / pos_entry if pos_entry else eq
        peak = max(peak, mtm); mdd = max(mdd, (peak - mtm) / peak)
        if pos_entry and last_of_day:
            gross = b["close"] / pos_entry
            eq = pos_eq * gross * (1 - FEE)
            trades += 1; wins += (1 - FEE) ** 2 * gross > 1
            pos_entry = None
            peak = max(peak, eq); mdd = max(mdd, (peak - eq) / peak)
            continue
        if t == 0 or last_of_day:
            continue
        up = fast[t] > slow[t] and fast[t - 1] <= slow[t - 1]
        down = fast[t] < slow[t] and fast[t - 1] >= slow[t - 1]
        nxt = bars[t + 1]["open"]
        if up and not pos_entry:
            pos_eq = eq * (1 - FEE); pos_entry = nxt
        elif down and pos_entry:
            gross = nxt / pos_entry
            eq = pos_eq * gross * (1 - FEE)
            trades += 1; wins += (1 - FEE) ** 2 * gross > 1
            pos_entry = None
    return {"total_return_pct": round((eq - 1) * 100, 4), "trades": trades,
            "win_rate_pct": round(100 * wins / trades, 4) if trades else 0.0, "max_drawdown_pct": round(mdd * 100, 4)}


def run(path):
    return backtest(resample(load(path)))


if __name__ == "__main__":
    import json, sys
    print(json.dumps(run(sys.argv[1])))
