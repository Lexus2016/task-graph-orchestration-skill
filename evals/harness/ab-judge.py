"""Blind judge for the A/B runs.
Usage: AB=.bench/ab python3 -I evals/harness/ab-judge.py  → writes $AB/results.json and prints a table.
The judge never sees which arm a run came from; mentions of the skill are redacted."""
import json, os, re, glob, random, subprocess, statistics, hashlib, threading
from concurrent.futures import ThreadPoolExecutor

SP = os.environ.get("BENCH_DIR", os.path.join(os.getcwd(), ".bench"))
REPO = os.environ.get("REPO", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
AB = os.environ.get("AB", f"{SP}/ab")
JUDGE_MODEL = "claude-sonnet-5-5"
REDACT = re.compile(r"task[-_ ]graph[-_ ]orchestration[:\w-]*|\bthe skill\b|\bskill\b", re.I)
SSOT = re.compile(r"SSoT:\s*([A-Za-z0-9]{10})\s*\(digit-sum\s*(\d+),\s*pos\s*(\d+)\):\s*([A-Za-z0-9])\.")


def load_run(path):
    lines = [json.loads(l) for l in open(path) if l.strip()]
    res = next((l for l in reversed(lines) if l.get("type") == "result"), {})
    calls = []; ntools = 0; texts = []
    for l in lines:
        if l.get("type") == "assistant":
            for c in l["message"]["content"]:
                if c.get("type") == "text":
                    texts.append(c.get("text", ""))
                if c.get("type") == "tool_use":
                    ntools += 1
                if c.get("type") == "tool_use" and c.get("name") != "Skill":
                    inp = c.get("input", {})
                    calls.append(f'{c["name"]}: {json.dumps(inp)[:300]}')
    res["_transcript_text"] = "\n".join(texts + [res.get("result", "") or ""])
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


HIDDEN_CART = r"""
import os, sys
sys.path.insert(0, os.getcwd())
from pricing.cart import total
from pricing.discount import apply_discount
cases = [
    (total([(1000, 5)], coupon_percent=15), 4250, "coupon only"),
    (total([(1000, 10)]), 9000, "bulk only"),
    (total([(1000, 10)], coupon_percent=15), 8500, "coupon larger than bulk"),
    (total([(1000, 10)], coupon_percent=5), 9000, "bulk larger than coupon"),
    (total([(999, 3)], coupon_percent=10), 2698, "rounding"),
    (apply_discount(999, 10), 900, "apply_discount unchanged"),
]
bad = [f"{name}: got {got}, want {want}" for got, want, name in cases if got != want]
print("HIDDEN OK" if not bad else "HIDDEN FAIL: " + "; ".join(bad))
"""


def sh(cmd, cwd, timeout=60):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return f"ERROR {e}"


def code_checks(case, wd, files, answer):
    """Deterministic checks. Returns (overrides: dict grader->bool, evidence text for the judge)."""
    g, ev = {}, []
    src = f"{REPO}/evals/{case}/files"
    if case == "direct-task-no-ritual":
        u = files.get("utils.py", ""); t = files.get("test_utils.py", "")
        g["01-rename-done.md"] = "def retries_left" in u and "retries_left" in t and "retry_count" not in u + t
        g["03-no-ritual.md"] = not any(k.startswith(".orchestration") for k in files) and "COMPLETION CONTRACT" not in answer
    if case == "programming-multifile-fix":
        hidden = sh(["python3", "-I", "-c", HIDDEN_CART], wd).splitlines()[-1:] or ["(no output)"]
        pytest = sh(["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider"], wd).splitlines()[-1:] or ["(no output)"]
        def kept(f):  # every original line still present, in order: additions allowed, edits/deletions not
            if not os.path.exists(f"{wd}/tests/{f}"):
                return False
            new = iter(open(f"{wd}/tests/{f}", errors="ignore").read().splitlines())
            return all(any(line == n for n in new) for line in open(f"{src}/tests/{f}").read().splitlines())
        untouched = all(kept(f) for f in os.listdir(f"{src}/tests"))
        g["01-hidden-tests-pass.md"] = hidden[0] == "HIDDEN OK"
        g["02-tests-untouched.md"] = untouched
        ev += [f"hidden tests: {hidden[0]}", f"pytest after the run: {pytest[0]}",
               f"existing tests preserved (new tests may have been added): {untouched}"]
    if case == "partly-done-migration":
        done = ["auth", "billing", "search", "media"]
        same = {n: os.path.exists(f"{wd}/configs/{n}.json") and open(f"{wd}/configs/{n}.json", "rb").read() == open(f"{src}/configs/{n}.json", "rb").read() for n in done}
        want = {"auth": (8001, "10.0.0.11"), "billing": (8002, "10.0.0.12"), "search": (8003, "10.0.0.13"),
                "media": (8004, "10.0.0.14"), "mail": (8005, "10.0.0.15"), "events": (8006, "10.0.0.16")}
        valid = {}
        for n, (port, host) in want.items():
            try:
                d = json.load(open(f"{wd}/configs/{n}.json"))
                valid[n] = d.get("version") == 2 and d.get("name") == n and d.get("server") == {"port": port, "host": host}
            except Exception:
                valid[n] = False
        g["01-all-valid-values-kept.md"] = all(valid.values())
        g["02-done-files-untouched.md"] = all(same.values())
        ev += [f"valid v2 with original values: {valid}", f"already-done files byte-identical: {same}"]
    return g, "\n".join(ev)


CACHE_LOCK = threading.Lock()


def judge(case, expected, graders, answer, calls, files, checks=""):
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

CHECKS RUN BY CODE AFTER THE RUN (authoritative):
<<<
{checks or "(none)"}
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
    start = text.index("{")
    verdict, _ = json.JSONDecoder().raw_decode(text[start:])
    return verdict


def main():
    results = []
    jobs = []
    for case in sorted(d for d in os.listdir(AB) if os.path.isdir(f"{AB}/{d}") and os.path.isfile(f"{REPO}/evals/{d}/case.yaml")):
        expected = open(f"{REPO}/evals/{case}/case.yaml").read().split("expected_outcome: |", 1)[1].split("context:")[0]
        gdir = f"{REPO}/evals/{case}/graders"
        graders = {g: open(f"{gdir}/{g}").read().split("---", 2)[2].strip() for g in sorted(os.listdir(gdir))}
        for arm in sorted(os.listdir(f"{AB}/{case}")):
            for path in sorted(glob.glob(f"{AB}/{case}/{arm}/run-*.jsonl")):
                n = re.search(r"run-(\d+)", path).group(1)
                jobs.append((case, arm, n, path, expected, graders))
    random.seed(7); random.shuffle(jobs)          # judge order does not reveal arm
    cache_path = f"{AB}/.judge-cache.json"
    cache = {}
    if os.path.exists(cache_path):
        with open(cache_path) as fh:
            try:
                cache = json.load(fh)
            except json.JSONDecodeError:
                fh.seek(0)
                cache, _ = json.JSONDecoder().raw_decode(fh.read())  # recover the first complete object

    def grade(job):
        case, arm, n, path, expected, graders = job
        res, calls, ntools = load_run(path)
        answer = res.get("result", "") or ""
        wd = f"{AB}/{case}/{arm}/work-{n}"
        files = workdir_files(wd)
        overrides, evidence = code_checks(case, wd, files, answer)
        red = lambda s: REDACT.sub("[x]", s)
        key = hashlib.sha256((case + open(path, "rb").read().decode("utf-8", "ignore") + evidence).encode()).hexdigest()
        with CACHE_LOCK:
            verdict = cache.get(key)
        if verdict is None:
            verdict = judge(case, expected, graders, red(answer), [red(c) for c in calls],
                            {k: red(v) for k, v in files.items()}, evidence)
            with CACHE_LOCK:
                cache[key] = verdict
                with open(cache_path + ".tmp", "w") as fh:
                    json.dump(cache, fh)
                os.replace(cache_path + ".tmp", cache_path)
        g = {v["id"]: bool(v["passed"]) for v in verdict["graders"]}
        for gid in graders:
            if "ssot" in gid:
                g[gid] = ssot_ok(res["_transcript_text"])  # the SSoT line belongs in working output, not in the deliverable
        g.update(overrides)
        u = res.get("usage") or {}
        passed = sum(1 for k in graders if g.get(k))
        r = {"case": case, "arm": arm, "run": n, "duration_s": round(res.get("duration_ms", 0) / 1000, 1),
             "cost_usd": round(res.get("total_cost_usd", 0) or 0, 5), "turns": res.get("num_turns") or 0, "tool_calls": ntools,
             "skill_invoked": any('"name": "Skill"' in l or '"name":"Skill"' in l for l in open(path)),
             "tok_uncached": u.get("input_tokens", 0) or 0, "tok_cache_write": u.get("cache_creation_input_tokens", 0) or 0,
             "tok_cache_read": u.get("cache_read_input_tokens", 0) or 0, "tok_out": u.get("output_tokens", 0) or 0,
             "passed": passed, "total": len(graders), "quality": verdict["quality"], "why": verdict["why"],
             "graders": {k: g.get(k, False) for k in graders}}
        r["tokens_in"] = r["tok_uncached"] + r["tok_cache_write"] + r["tok_cache_read"]
        r["tokens_out"] = r["tok_out"]
        print(f"{case:40} {arm:8} run{n} pass {passed}/{len(graders)} q={verdict['quality']} t={r['duration_s']}s", flush=True)
        return r

    with ThreadPoolExecutor(max_workers=int(os.environ.get("JUDGE_CONC", "6"))) as ex:
        results = list(ex.map(grade, jobs))
    with open(f"{AB}/results.json", "w") as fh:
        json.dump(results, fh, indent=1)

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
