"""Task-graph trace: render an animated graph page, or check runs against the skill.

  python3 trace_graph.py render <trace.jsonl> [--transcript run.jsonl] [--out graph.html]
      Writes a self-contained HTML replay (default: next to the trace) and prints its file:// URL.
  python3 trace_graph.py analyze --run NAME TRACE TRANSCRIPT [--run ...] [--bundle out.json] [--report out.md]
      Checks one or more runs and prints a Markdown report.

The transcript is optional: `claude -p --output-format stream-json --verbose` output. With it, events are tied to
the real tool calls and token use is split between the orchestrator and its subagents. Standard library only."""
import argparse, json, os, re, sys

TERMINAL = {"DONE", "FAILED", "SKIPPED"}
ENDS = {"DONE", "FAILED", "WAITING", "BLOCKED"}
BIG_BRIEF, BIG_RETURN = 4000, 3000


def read_jsonl(path):
    out = []
    for line in open(path, errors="ignore"):
        line = line.strip()
        if line.startswith("{"):
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def transcript_calls(path):
    """Tool calls in order, with timestamp, thread (main / subagent) and a short label; plus token usage per thread."""
    calls, usage_main, usage_sub, peak, t0 = [], [0, 0, 0, 0], [0, 0, 0, 0], 0, None
    for d in read_jsonl(path):
        if d.get("type") != "assistant":
            continue
        ts = d.get("timestamp")
        sub = d.get("parent_tool_use_id") is not None
        u = d["message"].get("usage") or {}
        vec = [u.get("input_tokens", 0) or 0, u.get("cache_creation_input_tokens", 0) or 0,
               u.get("cache_read_input_tokens", 0) or 0, u.get("output_tokens", 0) or 0]
        tgt = usage_sub if sub else usage_main
        for i in range(4):
            tgt[i] += vec[i]
        if not sub:
            peak = max(peak, vec[0] + vec[1] + vec[2])
        for c in d["message"].get("content", []):
            if c.get("type") != "tool_use":
                continue
            inp = c.get("input") or {}
            raw = json.dumps(inp)
            label = inp.get("command") or inp.get("file_path") or inp.get("path") or inp.get("pattern") or inp.get("description") or inp.get("id") or ""
            calls.append({"i": len(calls), "ts": ts, "tool": c.get("name"), "sub": sub,
                          "label": str(label)[:160], "raw": raw,
                          "trace_only": ".trace.jsonl" in raw and raw.count('\\"ev\\"') > 0 and not re.search(r"&&|;\s*(?!EOF)\w", str(inp.get("command", "")).split("EOF")[-1] if "EOF" in raw else "x")})
    res = next((d for d in reversed(read_jsonl(path)) if d.get("type") == "result"), {})
    return calls, {"main": usage_main, "sub": usage_sub, "peak_main_context": peak,
                   "duration_s": round((res.get("duration_ms") or 0) / 1000, 1), "cost_usd": res.get("total_cost_usd"),
                   "turns": res.get("num_turns"), "final_answer": (res.get("result") or "")[:4000]}


def locate(events, calls):
    """Attach each trace event to the tool call that wrote it (first call whose input contains its seq)."""
    for e in events:
        e["_call"] = None
        pat = re.compile(r'\\?"seq\\?"\s*:\s*%d\b' % e.get("seq", -1))
        for c in calls:
            if ".trace.jsonl" in c["raw"] and pat.search(c["raw"]):
                e["_call"] = c["i"]
                break
    return events


def check(events, calls):
    findings = []
    add = lambda sev, code, msg: findings.append({"severity": sev, "code": code, "message": msg})
    if not events:
        add("error", "no-trace", "The trace is empty.")
        return findings
    if events[0].get("ev") != "plan":
        add("error", "plan-not-first", "The first event is not a plan.")
    seqs = [e.get("seq") for e in events]
    if seqs != sorted(seqs) or len(set(seqs)) != len(seqs):
        add("warn", "seq-order", "seq numbers are not strictly increasing.")

    units, criteria, crit_evidence, unit_evidence = {}, {}, set(), set()
    norm = lambda x: " ".join(str(x or "").lower().split())
    tried, failed_causes, last_sig, loop_ssot_since = {}, set(), {}, {}  # failure memory
    status, last_end, checkpointed = {}, [], set()
    for e in events:
        ev = e.get("ev")
        if ev == "plan":
            for c in e.get("criteria", []):
                criteria[c["id"]] = c
            for u in e.get("units", []):
                units[u["id"]] = u
        elif ev == "failure":
            uid, cause, sig = e.get("unit"), norm(e.get("cause")), norm(e.get("signature"))
            if cause and cause in tried.setdefault(uid, set()):
                add("error", "repeated-cause", f"seq {e['seq']}: {uid} tested the cause '{e.get('cause')}' again — the failure ledger already marks it as failed.")
            if sig and last_sig.get(uid) == sig and not loop_ssot_since.get(uid):
                add("warn", "loop-without-ssot", f"seq {e['seq']}: {uid} failed twice with '{e.get('signature')}' and no loop SSoT in between.")
            if cause:
                tried[uid].add(cause); failed_causes.add(cause)
            last_sig[uid], loop_ssot_since[uid] = sig, False
        elif ev == "ssot" and e.get("trigger") == "loop":
            for uid in loop_ssot_since:
                loop_ssot_since[uid] = True
        elif ev == "replan":
            checkpointed.update(last_end)  # a replan is a checkpoint decision
            for u in e.get("add", []):
                if norm(u.get("cause")) and norm(u.get("cause")) in failed_causes:
                    add("error", "repeated-cause", f"seq {e['seq']}: replan adds {u.get('id')} to test '{u.get('cause')}', which already failed.")
                units[u["id"]] = u
            for uid in e.get("remove", []):
                status[uid] = "REMOVED"
        elif ev == "evidence":
            unit_evidence.add(e.get("unit"))
            if e.get("criterion"):
                crit_evidence.add(e["criterion"])
        elif ev == "status":
            uid, to = e.get("unit"), e.get("to")
            if uid not in units:
                add("warn", "unknown-unit", f"seq {e['seq']}: status for unit {uid} that is not in the plan.")
            if to == "DONE" and uid not in unit_evidence:
                same_batch = [x for x in events if x.get("ev") == "evidence" and x.get("unit") == uid and x["seq"] > e["seq"]
                              and ((x.get("_call") is not None and x.get("_call") == e.get("_call")) or x["seq"] == e["seq"] + 1)]
                if same_batch:
                    add("warn", "evidence-after-done", f"seq {e['seq']}: {uid} marked DONE one step before its evidence (same batch) — write evidence first.")
                else:
                    add("error", "done-without-evidence", f"seq {e['seq']}: {uid} marked DONE with no evidence event before it.")
            if to == "RUNNING" and last_end:
                missing = [u for u in last_end if u not in checkpointed]
                if missing:
                    add("warn", "no-checkpoint", f"seq {e['seq']}: {uid} started before a checkpoint after {', '.join(missing)}.")
                last_end = []
            if to in ENDS:
                last_end.append(uid)
            status[uid] = to
        elif ev == "checkpoint":
            checkpointed.update(last_end if e.get("after") in (None, "*") else [e.get("after")] + last_end)
        elif ev == "skip":
            uid = e.get("unit")
            if e.get("reason") not in ("optional", "superseded"):
                add("error", "skip-without-reason", f"seq {e['seq']}: {uid} skipped without reason optional/superseded.")
            u = units.get(uid, {})
            if e.get("reason") == "superseded" and any(c not in crit_evidence for c in u.get("criteria", [])):
                add("warn", "skip-before-evidence", f"seq {e['seq']}: {uid} skipped as superseded while its criteria lack evidence.")
            status[uid] = "SKIPPED"
        elif ev == "delegate":
            if (e.get("brief_chars") or 0) > BIG_BRIEF:
                add("warn", "heavy-brief", f"seq {e['seq']}: brief of {e['brief_chars']} chars to {e.get('worker')} — pass paths, not contents.")
        elif ev == "return":
            if (e.get("return_chars") or 0) > BIG_RETURN:
                add("warn", "raw-return", f"seq {e['seq']}: {e.get('worker')} returned {e['return_chars']} chars — ask for conclusions, not raw material.")

    finals = [e for e in events if e.get("ev") == "final"]
    if not finals:
        add("error", "no-final", "No final event.")
    else:
        f = finals[-1]
        ssot_final = [e for e in events if e.get("ev") == "ssot" and e.get("trigger") == "final" and e["seq"] < f["seq"]]
        if not ssot_final:
            add("warn", "no-final-ssot", "No final-decision SSoT before the final event.")
        missing = [cid for cid, c in criteria.items() if c.get("required") and cid not in crit_evidence]
        if f.get("result") == "complete" and missing:
            add("error", "complete-without-evidence", f"Final says complete but required criteria lack evidence: {', '.join(missing)}.")
        open_units = [u for u in units if status.get(u) not in TERMINAL | {"REMOVED"}]
        if open_units:
            add("warn", "units-left-open", f"Units without a terminal status at the end: {', '.join(open_units)}.")

    if calls:
        located = [e for e in events if e.get("_call") is not None]
        if len(located) < len(events):
            add("info", "unlocated-events", f"{len(events) - len(located)} of {len(events)} events could not be matched to a tool call.")
        # work between RUNNING and DONE for self-owned units
        for e in events:
            if e.get("ev") == "status" and e.get("to") == "DONE" and e.get("_call") is not None:
                uid = e["unit"]
                start = next((x for x in events if x.get("ev") == "status" and x.get("unit") == uid and x.get("to") == "RUNNING"
                              and x["seq"] < e["seq"] and x.get("_call") is not None), None)
                if start and units.get(uid, {}).get("owner", "self") == "self":
                    work = [c for c in calls[start["_call"] + 1:e["_call"]] if ".trace.jsonl" not in c["raw"]]
                    if not work and start["_call"] != e["_call"]:
                        add("warn", "done-without-work", f"seq {e['seq']}: {uid} went RUNNING → DONE with no tool call in between.")
        writes = [c for c in calls if ".trace.jsonl" in c["raw"] and not c["sub"]]
        alone = [c for c in writes if c["trace_only"]]
        main_calls = [c for c in calls if not c["sub"]]
        if main_calls and len(alone) / len(main_calls) > 0.3:
            add("warn", "trace-overhead", f"{len(alone)} of {len(main_calls)} main-thread tool calls only write the trace — batch events with real actions.")
    return findings


def build(label, trace, transcript):
    events = read_jsonl(trace) if trace and os.path.exists(trace) else []
    calls, meta = transcript_calls(transcript) if transcript and os.path.exists(transcript) else ([], {})
    locate(events, calls)
    findings = check(events, calls)
    for c in calls:
        c.pop("raw", None)
    return {"label": label, "events": events, "calls": calls, "meta": meta, "findings": findings}


def report(runs):
    lines = ["# Trace analysis", ""]
    for r in runs:
        m = r["meta"]
        lines += [f"## {r['label']}", ""]
        if m:
            main, sub = m["main"], m["sub"]
            lines.append(f"- {len(r['events'])} trace events · {len([c for c in r['calls'] if not c['sub']])} main tool calls · "
                         f"{len([c for c in r['calls'] if c['sub']])} subagent tool calls · {m['duration_s']} s · ${m['cost_usd'] or 0:.4f}")
            lines.append(f"- Orchestrator tokens {sum(main):,} (peak context {m['peak_main_context']:,}) · subagent tokens {sum(sub):,}" if sum(main)
                         else "- Token split unavailable for this runtime's transcript")
        delegs = [e for e in r["events"] if e.get("ev") == "delegate"]
        if delegs:
            lines.append(f"- Delegations: {len(delegs)}, brief chars avg {sum(e.get('brief_chars', 0) for e in delegs) // len(delegs)}")
        lines.append("")
        for f in r["findings"] or [{"severity": "ok", "code": "clean", "message": "No findings."}]:
            lines.append(f"- **{f['severity']}** `{f['code']}` — {f['message']}")
        lines.append("")
    return "\n".join(lines)


def render(trace, transcript=None, out=None, label=None):
    run = build(label or os.path.basename(trace).replace(".trace.jsonl", ""), trace, transcript)
    tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "trace-viewer.html")
    html = open(tpl).read().replace("/*__BUNDLE__*/null", json.dumps({"runs": [run]}).replace("</", "<\\/"))
    out = out or os.path.join(os.path.dirname(os.path.abspath(trace)), os.path.basename(trace).replace(".trace.jsonl", "") + ".graph.html")
    with open(out, "w") as fh:
        fh.write(html)
    return "file://" + os.path.abspath(out), run


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render"); r.add_argument("trace"); r.add_argument("--transcript"); r.add_argument("--out"); r.add_argument("--label")
    a = sub.add_parser("analyze"); a.add_argument("--run", nargs=3, action="append", required=True, metavar=("NAME", "TRACE", "TRANSCRIPT"))
    a.add_argument("--bundle"); a.add_argument("--report"); a.add_argument("--html")
    args = ap.parse_args()
    if args.cmd == "render":
        url, run = render(args.trace, args.transcript, args.out, args.label)
        bad = [f for f in run["findings"] if f["severity"] in ("error", "warn")]
        print(url)
        print(f"{len(run['events'])} events, {len(bad)} findings" + (": " + "; ".join(f["code"] for f in bad) if bad else ""))
        return
    runs = [build(*spec) for spec in args.run]
    if args.bundle:
        with open(args.bundle, "w") as fh:
            json.dump({"runs": runs}, fh)
    if args.html:
        tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "trace-viewer.html")
        with open(args.html, "w") as fh:
            fh.write(open(tpl).read().replace("/*__BUNDLE__*/null", json.dumps({"runs": runs}).replace("</", "<\\/")))
    text = report(runs)
    if args.report:
        with open(args.report, "w") as fh:
            fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
