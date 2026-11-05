"""Blind judge for the A/B runs.
Usage: AB=.bench/ab python3 -I evals/harness/ab-judge.py  → writes $AB/results.json and prints a table.
The judge never sees which arm a run came from; mentions of the skill are redacted."""
import json, os, re, glob, random, subprocess, statistics

SP = os.environ.get("BENCH_DIR", os.path.join(os.getcwd(), ".bench"))
REPO = os.environ.get("REPO", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
AB = os.environ.get("AB", f"{SP}/ab")
JUDGE_MODEL = "claude-sonnet-5-5"
REDACT = re.compile(r"task[-_ ]graph[-_ ]orchestration[:\w-]*|\bthe skill\b|\bskill\b", re.I)
SSOT = re.compile(r"SSoT:\s*([A-Za-z0-9]{10})\s*\(digit-sum\s*(\d+),\s*pos\s*(\d+)\):\s*([A-Za-z0-9])\.")


def load_run(path):
    lines = [json.loads(l) for l in open(path) if l.strip()]
    res = next((l for l in reversed(lines) if l.get("type") == "result"), {})
    calls = []; ntools = 0
    for l in lines:
        if l.get("type") == "assistant":
            for c in l["message"]["content"]:
                if c.get("type") == "tool_use":
                    ntools += 1
                if c.get("type") == "tool_use" and c.get("name") != "Skill":
                    inp = c.get("input", {})
                    calls.append(f'{c["name"]}: {json.dumps(inp)[:300]}')
    return res, calls, ntools


def ssot_ok(text):
    """Deterministic check: an SSoT line exists and its arithmetic is right."""
    for s, S, N, ch in SSOT.findall(text):
        digits = sum(int(x) for x in s if x.isdigit())
        if digits == int(S) and digits % 10 == int(N) and s[int(N)] == ch:
            return True
    return False


def workdir_files(wd):
    out = {}
    for p in glob.glob(f"{wd}/**/*", recursive=True):
        if os.path.isfile(p) and os.path.getsize(p) < 20000 and not p.endswith((".pyc",)):
            rel = os.path.relpath(p, wd)
            if rel.startswith((".", "__pycache__")) or "/." in rel:
                continue
            out[rel] = open(p, errors="ignore").read()
    return out


def judge(case, expected, graders, answer, calls, files):
    prompt = f"""You are grading one AI agent run. Be strict and literal. Grade only what the evidence shows.

TASK EXPECTATION:
{expected}

CRITERIA (grade each independently, true/false):
{json.dumps(graders, indent=1)}

AGENT FINAL ANSWER:
<<<
{answer}
>>>

TOOL CALLS (in order):
<<<
{chr(10).join(calls) or "(none)"}
>>>

FILES IN WORKING DIRECTORY AFTER THE RUN:
<<<
{json.dumps(files, indent=1)[:12000]}
>>>

Also give an overall quality score from 1 to 10 for how well the run did the task a demanding engineer asked for:
correctness, honesty about failures, usefulness of the next step, no padding. 10 = nothing to improve.

Reply with ONLY this JSON:
{{"graders": [{{"id": "<file name>", "passed": true|false, "evidence": "<short>"}}], "quality": <1-10>, "why": "<one sentence>"}}"""
    for attempt in range(2):
        try:
            return _judge_once(prompt)
        except Exception as e:  # malformed judge output: retry once, then fail loudly
            err = e
    raise err


def _judge_once(prompt):
    r = subprocess.run(
        ["claude", "-p", "--model", JUDGE_MODEL, "--setting-sources", "project,local", "--strict-mcp-config",
         "--mcp-config", f"{SP}/empty-mcp.json", "--max-turns", "1", "--output-format", "json"],
        input=prompt, capture_output=True, text=True, cwd=SP, timeout=300)
    out = json.loads(r.stdout)
    if isinstance(out, list):
        out = next(o for o in reversed(out) if isinstance(o, dict) and o.get("type") == "result")
    text = out.get("result", "")
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def main():
    results = []
    jobs = []
    for case in sorted(d for d in os.listdir(AB) if os.path.isdir(f"{AB}/{d}")):
        expected = open(f"{REPO}/evals/{case}/case.yaml").read().split("expected_outcome: |", 1)[1].split("context:")[0]
        gdir = f"{REPO}/evals/{case}/graders"
        graders = {g: open(f"{gdir}/{g}").read().split("---", 2)[2].strip() for g in sorted(os.listdir(gdir))}
        for arm in sorted(os.listdir(f"{AB}/{case}")):
            for path in sorted(glob.glob(f"{AB}/{case}/{arm}/run-*.jsonl")):
                n = re.search(r"run-(\d+)", path).group(1)
                jobs.append((case, arm, n, path, expected, graders))
    random.seed(7); random.shuffle(jobs)          # judge order does not reveal arm
    for case, arm, n, path, expected, graders in jobs:
        res, calls, ntools = load_run(path)
        answer = res.get("result", "") or ""
        wd = f"{AB}/{case}/{arm}/work-{n}"
        files = workdir_files(wd)
        red = lambda s: REDACT.sub("[x]", s)
        verdict = judge(case, expected, graders, red(answer), [red(c) for c in calls],
                        {k: red(v) for k, v in files.items()})
        g = {v["id"]: bool(v["passed"]) for v in verdict["graders"]}
        # deterministic overrides
        for gid in graders:
            if "ssot" in gid:
                g[gid] = ssot_ok(answer) and (gid != "01-ssot-before-report.md" or answer.find("SSoT:") < max(1, len(answer) // 2))
        if case == "direct-task-no-ritual":
            u = files.get("utils.py", ""); t = files.get("test_utils.py", "")
            g["01-rename-done.md"] = "def retries_left" in u and "retries_left" in t and "retry_count" not in u + t
            g["03-no-ritual.md"] = not any(k.startswith(".orchestration") for k in files) and "COMPLETION CONTRACT" not in answer
        passed = sum(1 for k in graders if g.get(k))
        results.append({"case": case, "arm": arm, "run": n, "duration_s": round(res.get("duration_ms", 0) / 1000, 1),
                        "cost_usd": round(res.get("total_cost_usd", 0) or 0, 4), "turns": res.get("num_turns"), "tool_calls": ntools,
                        "tokens_in": sum((res.get("usage") or {}).get(k, 0) or 0 for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")),
                        "tokens_out": (res.get("usage") or {}).get("output_tokens", 0) or 0,
                        "passed": passed, "total": len(graders), "quality": verdict["quality"], "why": verdict["why"],
                        "graders": {k: g.get(k, False) for k in graders}})
        print(f"{case:40} {arm:8} run{n} pass {passed}/{len(graders)} q={verdict['quality']} t={results[-1]['duration_s']}s", flush=True)
    json.dump(results, open(f"{AB}/results.json", "w"), indent=1)

    print("\n| case | arm | pass rate | quality (1-10) | time s | turns | tool calls | tokens in | tokens out | cost $ |")
    for case in sorted({r["case"] for r in results}):
        for arm in sorted({r["arm"] for r in results}):
            rs = [r for r in results if r["case"] == case and r["arm"] == arm]
            if not rs: continue
            pr = sum(r["passed"] for r in rs) / sum(r["total"] for r in rs)
            print(f"| {case} | {arm} | {pr*100:.0f}% | {statistics.mean(r['quality'] for r in rs):.1f} | "
                  f"{statistics.mean(r['duration_s'] for r in rs):.1f} | {statistics.mean(r['turns'] for r in rs):.1f} | "
                  f"{statistics.mean(r['tool_calls'] for r in rs):.1f} | {statistics.mean(r['tokens_in'] for r in rs):.0f} | "
                  f"{statistics.mean(r['tokens_out'] for r in rs):.0f} | {statistics.mean(r['cost_usd'] for r in rs):.4f} |")


if __name__ == "__main__":
    main()
