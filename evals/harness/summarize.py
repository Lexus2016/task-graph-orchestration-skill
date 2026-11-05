"""Summarize judged A/B runs of several models into Markdown tables.
Usage: python3 -I evals/harness/summarize.py <label>=<results.json> [...]  > tables.md
Also writes evals/benchmark/summary.json next to this script's repo."""
import json, os, statistics as st, sys

TARGET = {"final-check-catches-unverified-claim", "loop-trigger-changes-strategy"}
CONTROL = {"batch-with-broken-item", "direct-task-no-ritual"}
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def agg(rs):
    og = [v for r in rs for k, v in r["graders"].items() if "ssot" not in k and "no-ritual" not in k]
    return {"n": len(rs), "quality": st.mean(r["quality"] for r in rs),
            "outcome_pass": sum(og) / len(og) if og else None,
            "all_pass": sum(r["passed"] for r in rs) / sum(r["total"] for r in rs),
            "time_s": st.mean(r["duration_s"] for r in rs), "turns": st.mean(r["turns"] for r in rs),
            "tool_calls": st.mean(r["tool_calls"] for r in rs),
            "tokens": st.mean(r["tokens_in"] + r["tokens_out"] for r in rs),
            "tokens_out": st.mean(r["tokens_out"] for r in rs), "cost_usd": st.mean(r["cost_usd"] for r in rs)}


def main():
    models = [a.split("=", 1) for a in sys.argv[1:]]
    summary = {}
    for label, path in models:
        R = json.load(open(path))
        summary[label] = {
            grp: {arm: agg([r for r in R if r["arm"] == arm and r["case"] in cases])
                  for arm in ("without", "forced", "auto") if any(r["arm"] == arm for r in R)}
            for grp, cases in (("target", TARGET), ("control", CONTROL))}
        summary[label]["cases"] = {
            c: {arm: agg([r for r in R if r["arm"] == arm and r["case"] == c])
                for arm in ("without", "forced", "auto") if any(r["arm"] == arm and r["case"] == c for r in R)}
            for c in sorted({r["case"] for r in R})}
    os.makedirs(f"{REPO}/evals/benchmark", exist_ok=True)
    json.dump(summary, open(f"{REPO}/evals/benchmark/summary.json", "w"), indent=1)

    f = lambda x, d=1: f"{x:.{d}f}"
    out = []
    out.append("| Model | Runs per arm | Without skill | With skill (loaded) | Δ | With skill (auto-trigger) | Δ |")
    out.append("|---|---|---|---|---|---|---|")
    for label, _ in models:
        t = summary[label]["target"]
        out.append(f"| {label} | {t['without']['n'] // 2} | {f(t['without']['quality'],2)} | {f(t['forced']['quality'],2)} | "
                   f"**{t['forced']['quality'] - t['without']['quality']:+.2f}** | {f(t['auto']['quality'],2)} | "
                   f"{t['auto']['quality'] - t['without']['quality']:+.2f} |")
    out.append("")
    out.append("| Model | Time | Turns | Tool calls | Tokens | Cost |")
    out.append("|---|---|---|---|---|---|")
    for label, _ in models:
        a, b = summary[label]["target"]["without"], summary[label]["target"]["forced"]
        out.append(f"| {label} | {f(a['time_s'])} → {f(b['time_s'])} s (×{b['time_s']/a['time_s']:.1f}) | "
                   f"{f(a['turns'])} → {f(b['turns'])} | {f(a['tool_calls'])} → {f(b['tool_calls'])} | "
                   f"{a['tokens']/1000:.0f}k → {b['tokens']/1000:.0f}k (×{b['tokens']/a['tokens']:.1f}) | "
                   f"${a['cost_usd']:.4f} → ${b['cost_usd']:.4f} (×{b['cost_usd']/a['cost_usd']:.1f}) |")
    out.append("")
    out.append("| Model | Without skill | With skill (loaded) | With skill (auto-trigger) |")
    out.append("|---|---|---|---|")
    for label, _ in models:
        c = summary[label]["control"]
        out.append(f"| {label} | {f(c['without']['quality'],2)} | {f(c['forced']['quality'],2)} | {f(c['auto']['quality'],2)} |")
    print("\n".join(out))

    # full per-case table
    lines = ["# Benchmark results (per case)", "",
             "Quality = blind judge score 1–10. Outcome = share of non-SSoT graders passed. Means over runs.", "",
             "| Model | Case | Arm | n | Quality | Outcome | All graders | Time s | Turns | Tool calls | Tokens | Cost $ |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for label, _ in models:
        for c, arms in summary[label]["cases"].items():
            for arm, a in arms.items():
                op = "—" if a["outcome_pass"] is None else f"{a['outcome_pass']*100:.0f}%"
                lines.append(f"| {label} | {c} | {arm} | {a['n']} | {a['quality']:.2f} | {op} | {a['all_pass']*100:.0f}% | "
                             f"{a['time_s']:.1f} | {a['turns']:.1f} | {a['tool_calls']:.1f} | {a['tokens']:.0f} | {a['cost_usd']:.4f} |")
    open(f"{REPO}/evals/benchmark/RESULTS.md", "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
