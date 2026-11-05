"""Summarize judged A/B runs into Markdown tables (percentages, cache-aware cost).
Usage: python3 -I evals/harness/summarize.py "<label>=<results.json>" [...]  > tables.md
Writes evals/benchmark/summary.json and evals/benchmark/RESULTS.md."""
import json, os, statistics as st, sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CATEGORIES = {
    "discipline": ["loop-trigger-changes-strategy", "final-check-catches-unverified-claim"],
    "real": ["research-conflicting-sources", "programming-multifile-fix", "partly-done-migration"],
    "small": ["batch-with-broken-item", "direct-task-no-ritual"],
}
CAT_TITLE = {"discipline": "Discipline tasks (repeated failure, report built on subagent claims)",
             "real": "Real work (research with conflicting sources, multi-file bug fix, half-finished migration)",
             "small": "Small tasks (should stay small)"}
ARMS = ("without", "forced", "auto")
TOK = ("tok_uncached", "tok_cache_write", "tok_cache_read", "tok_out")


def mean(xs):
    xs = list(xs)
    return st.mean(xs) if xs else float("nan")


def agg(rs):
    og = [v for r in rs for k, v in r["graders"].items() if "ssot" not in k and "no-ritual" not in k]
    a = {"n": len(rs), "quality_pct": mean(r["quality"] * 10 for r in rs),
         "outcome_pct": 100 * sum(og) / len(og) if og else float("nan"),
         "time_s": mean(r["duration_s"] for r in rs), "turns": mean(r["turns"] for r in rs),
         "tool_calls": mean(r["tool_calls"] for r in rs), "cost_usd": mean(r["cost_usd"] for r in rs),
         "skill_rate": 100 * mean(1 if r.get("skill_invoked") else 0 for r in rs)}
    for k in TOK:
        a[k] = mean(r.get(k, 0) for r in rs)
    a["tokens"] = sum(a[k] for k in TOK)
    a["cache_read_share"] = 100 * a["tok_cache_read"] / a["tokens"] if a["tokens"] else float("nan")
    return a


def main():
    models = [a.split("=", 1) for a in sys.argv[1:]]
    summary = {}
    for label, path in models:
        R = json.load(open(path))
        s = {"categories": {}, "cases": {}}
        for cat, cases in CATEGORIES.items():
            s["categories"][cat] = {arm: agg([r for r in R if r["arm"] == arm and r["case"] in cases])
                                    for arm in ARMS if any(r["arm"] == arm and r["case"] in cases for r in R)}
        s["categories"]["work"] = {arm: agg([r for r in R if r["arm"] == arm and r["case"] not in CATEGORIES["small"]]) for arm in ARMS}
        for c in sorted({r["case"] for r in R}):
            s["cases"][c] = {arm: agg([r for r in R if r["arm"] == arm and r["case"] == c]) for arm in ARMS
                             if any(r["arm"] == arm and r["case"] == c for r in R)}
        summary[label] = s
    os.makedirs(f"{REPO}/evals/benchmark", exist_ok=True)
    json.dump(summary, open(f"{REPO}/evals/benchmark/summary.json", "w"), indent=1)

    pct = lambda x: f"{x:.0f}%"
    pp = lambda d: f"{d:+.0f} pp"
    rel = lambda a, b: f"{(b - a) / a * 100:+.0f}%" if a else "—"
    out = []
    for cat in ("discipline", "real", "small"):
        out.append(f"**{CAT_TITLE[cat]}** — quality, % of ideal")
        out.append("")
        out.append("| Model | Without skill | Skill loaded | Δ | Relative | Skill auto | Δ |")
        out.append("|---|---|---|---|---|---|---|")
        for label, _ in models:
            c = summary[label]["categories"][cat]
            w, f, a = c["without"]["quality_pct"], c["forced"]["quality_pct"], c["auto"]["quality_pct"]
            out.append(f"| {label} | {pct(w)} | {pct(f)} | **{pp(f - w)}** | {rel(w, f)} | {pct(a)} | {pp(a - w)} |")
        out.append("")
    out.append("**Cost of using the skill** — all non-small tasks, *without → loaded*")
    out.append("")
    out.append("| Model | Time | Tool calls | Tokens | of them cache reads | Uncached input + output | Cost |")
    out.append("|---|---|---|---|---|---|---|")
    for label, _ in models:
        a, b = summary[label]["categories"]["work"]["without"], summary[label]["categories"]["work"]["forced"]
        fresh_a = a["tok_uncached"] + a["tok_cache_write"] + a["tok_out"]
        fresh_b = b["tok_uncached"] + b["tok_cache_write"] + b["tok_out"]
        out.append(f"| {label} | ×{b['time_s'] / a['time_s']:.1f} | {a['tool_calls']:.1f} → {b['tool_calls']:.1f} | "
                   f"×{b['tokens'] / a['tokens']:.1f} | {pct(a['cache_read_share'])} → {pct(b['cache_read_share'])} | "
                   f"×{fresh_b / fresh_a:.1f} | ×{b['cost_usd'] / a['cost_usd']:.1f} (${a['cost_usd']:.4f} → ${b['cost_usd']:.4f}) |")
    out.append("")
    out.append("**How often the model picks the skill up by itself** (auto arm)")
    out.append("")
    out.append("| Model | Discipline | Real work | Small tasks |")
    out.append("|---|---|---|---|")
    for label, _ in models:
        c = summary[label]["categories"]
        out.append(f"| {label} | {pct(c['discipline']['auto']['skill_rate'])} | {pct(c['real']['auto']['skill_rate'])} | {pct(c['small']['auto']['skill_rate'])} |")
    print("\n".join(out))

    lines = ["# Benchmark results (per task)", "",
             "Quality = blind judge score as % of ideal (score × 10). Outcome = share of task criteria passed (SSoT-format criteria excluded). Means over runs.",
             "Tokens are split by billing class: uncached input, cache write, cache read, output.", "",
             "| Model | Task | Arm | n | Quality | Outcome | Time s | Turns | Tool calls | Uncached in | Cache write | Cache read | Output | Cost $ | Skill used |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for label, _ in models:
        for c, arms in summary[label]["cases"].items():
            for arm, a in arms.items():
                lines.append(f"| {label} | {c} | {arm} | {a['n']} | {a['quality_pct']:.0f}% | {a['outcome_pct']:.0f}% | {a['time_s']:.1f} | "
                             f"{a['turns']:.1f} | {a['tool_calls']:.1f} | {a['tok_uncached']:.0f} | {a['tok_cache_write']:.0f} | "
                             f"{a['tok_cache_read']:.0f} | {a['tok_out']:.0f} | {a['cost_usd']:.4f} | {a['skill_rate']:.0f}% |")
    open(f"{REPO}/evals/benchmark/RESULTS.md", "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
