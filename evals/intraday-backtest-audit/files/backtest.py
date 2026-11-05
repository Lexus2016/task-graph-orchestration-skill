"""Backtest of the EMA 9/21 intraday strategy (see STRATEGY.md). Usage: python3 backtest.py candles.csv"""
import csv
import json
import sys
from datetime import datetime

FEE = 0.0005  # taker, per side


def load(path):
    with open(path) as fh:
        return [(r["ts"], float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"])) for r in csv.DictReader(fh)]


def resample(rows):
    bars = []
    for ts, o, h, l, c in rows:
        t = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
        key = (t.date(), t.hour, t.minute // 5)
        if bars and bars[-1]["key"] == key:
            b = bars[-1]
            b["high"], b["low"], b["close"] = max(b["high"], h), min(b["low"], l), c
        else:
            bars.append({"key": key, "day": t.date(), "open": o, "high": h, "low": l, "close": c})
    return bars


def ema(values, n):
    a, out = 2 / (n + 1), []
    for v in values:
        out.append(v if not out else a * v + (1 - a) * out[-1])
    return out


def crosses(fast, slow):
    """+1 / -1 / 0 per bar. Shifted by one so the order fills on the bar where the cross happens."""
    sig = [0] * len(fast)
    for t in range(len(fast) - 1):
        if fast[t + 1] > slow[t + 1] and fast[t] <= slow[t]:
            sig[t] = 1
        elif fast[t + 1] < slow[t + 1] and fast[t] >= slow[t]:
            sig[t] = -1
    return sig


def run(bars):
    closes = [b["close"] for b in bars]
    sig = crosses(ema(closes, 9), ema(closes, 21))
    eq, peak, mdd, entry, trades, wins = 1.0, 1.0, 0.0, None, 0, 0
    for t in range(len(bars) - 1):
        mtm = eq * bars[t]["close"] / entry if entry else eq
        peak = max(peak, mtm)
        mdd = max(mdd, (peak - mtm) / peak)
        nxt = bars[t + 1]["open"]
        if sig[t] == 1 and entry is None:
            entry = nxt
        elif sig[t] == -1 and entry is not None:
            r = nxt / entry
            eq *= r
            trades += 1
            wins += r > 1
            entry = None
    return {"total_return_pct": round((eq - 1) * 100, 4), "trades": trades,
            "win_rate_pct": round(100 * wins / trades, 4) if trades else 0.0, "max_drawdown_pct": round(mdd * 100, 4)}


if __name__ == "__main__":
    print(json.dumps(run(resample(load(sys.argv[1] if len(sys.argv) > 1 else "candles.csv"))), indent=2))
