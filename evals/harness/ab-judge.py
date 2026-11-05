"""Blind judge for the A/B runs.
Usage: AB=.bench/ab python3 -I evals/harness/ab-judge.py  → writes $AB/results.json and prints a table.
The judge never sees which arm a run came from; mentions of the skill are redacted."""
import json, os, re, glob, random, subprocess, statistics, hashlib, threading
from concurrent.futures import ThreadPoolExecutor

SP = os.environ.get("BENCH_DIR", os.path.join(os.getcwd(), ".bench"))
REPO = os.environ.get("REPO", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
AB = os.environ.get("AB", f"{SP}/ab")
JUDGE_MODEL = "claude-sonnet-5-5"
JUDGE_VERSION = "ssot-2"  # bump to invalidate cached verdicts when the judge prompt changes
REDACT = re.compile(r"task[-_ ]graph[-_ ]orchestration[:\w-]*|\bthe skill\b|\bskill\b", re.I)
SSOT = re.compile(r"SSoT:\s*([A-Za-z0-9]{10})\s*\(digit-sum\s*(\d+),\s*pos\s*(\d+)\):\s*([A-Za-z0-9])\.")


def load_run(path):
    lines = [json.loads(l) for l in open(path) if l.strip()]
    res = next((l for l in reversed(lines) if l.get("type") == "result"), {})
    calls = []; ntools = 0; texts = []
    split = {"orch_tokens": 0, "sub_tokens": 0, "peak_context": 0, "delegations": 0}
    for l in lines:
        if l.get("type") == "assistant":
            u = l["message"].get("usage") or {}
            ctx = (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
            if l.get("parent_tool_use_id") is None:
                split["orch_tokens"] += ctx + (u.get("output_tokens") or 0)
                split["peak_context"] = max(split["peak_context"], ctx)
                split["delegations"] += sum(1 for c in l["message"]["content"] if c.get("type") == "tool_use" and c.get("name") in ("Task", "Agent", "task"))
            else:
                split["sub_tokens"] += ctx + (u.get("output_tokens") or 0)
            for c in l["message"]["content"]:
                if c.get("type") == "text":
                    texts.append(c.get("text", ""))
                if c.get("type") == "tool_use":
                    ntools += 1
                if c.get("type") == "tool_use" and c.get("name") != "Skill":
                    inp = c.get("input", {})
                    calls.append(f'{c["name"]}: {json.dumps(inp)[:300]}')
    res["_transcript_text"] = "\n".join(texts + [res.get("result", "") or ""])
    res["_split"] = split
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


HIDDEN_CLIENT = r"""
import os, sys
sys.path.insert(0, os.getcwd())
from services.payments.client import PSPError, Timeout, call_with_retry
def run(seq, **kw):
    calls, sleeps, it = [], [], iter(seq)
    def send():
        calls.append(1); x = next(it)
        if isinstance(x, Exception): raise x
        return x
    try: r = call_with_retry(send, sleep=lambda s: sleeps.append(s), **kw)
    except Exception as e: r = e
    return r, len(calls), sleeps
bad = []
r, n, _ = run([PSPError(400, "bad")] + ["ok"] * 5)
if n != 1 or not isinstance(r, PSPError): bad.append("400 retried")
r, n, sl = run([Timeout(), Timeout(), "ok"])
if r != "ok" or n != 3: bad.append("timeout not retried")
if len(sl) < 2 or not (sl[1] > sl[0] > 0): bad.append("no increasing backoff")
r, n, _ = run([PSPError(503)] * 10)
if n > 5: bad.append(f"default attempts {n} > 5 (the configured cap)")
r, n, _ = run([PSPError(429), "ok"])
if r != "ok": bad.append("429 not retried")
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
    if case == "checkout-incident":
        m = re.search(r"timeout_ms:\s*(\d+)", files.get("config/payments.yaml", ""))
        g["01-config-fixed.md"] = bool(m) and int(m.group(1)) >= 1000
        hidden = (sh(["python3", "-I", "-c", HIDDEN_CLIENT], wd).splitlines() or ["(no output)"])[-1]
        g["02-client-fixed.md"] = hidden == "HIDDEN OK"
        pytest = (sh(["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider"], wd).splitlines() or ["(no output)"])[-1]
        def kept(f):
            if not os.path.exists(f"{wd}/tests/{f}"):
                return False
            new = iter(open(f"{wd}/tests/{f}", errors="ignore").read().splitlines())
            return all(any(line == x for x in new) for line in open(f"{src}/tests/{f}").read().splitlines())
        preserved = all(kept(f) for f in os.listdir(f"{src}/tests"))
        g["03-tests-kept-green.md"] = preserved and " passed" in pytest and "failed" not in pytest and "error" not in pytest
        ev += [f"config timeout_ms: {m.group(1) if m else 'not found'}", f"hidden client tests: {hidden}",
               f"pytest after the run: {pytest}", f"existing tests preserved: {preserved}"]
    if case == "vendor-contracts-review":
        truth = {"brightdesk": "VIOLATION", "cobalt-mail": "VIOLATION", "dataforge": "VIOLATION", "gridsight": "VIOLATION",
                 "helix-hr": "VIOLATION", "ionstack": "VIOLATION", "acme-analytics": "OK", "everpay": "OK", "fluxcdn": "OK", "jetform": "OK"}
        got = {}
        for line in files.get("report.md", "").splitlines():
            m = re.search(r"\b(" + "|".join(map(re.escape, truth)) + r")(?:\.md)?\W*:\s*\**\s*(OK|VIOLATION)", line)
            if m and m.group(1) not in got:
                got[m.group(1)] = m.group(2)
        g["01-verdicts-exact.md"] = got == truth
        g["02-amendments-applied.md"] = got.get("dataforge") == "VIOLATION" and got.get("gridsight") == "VIOLATION" and got.get("everpay") == "OK"
        wrong = sorted(k for k in truth if got.get(k) != truth[k])
        ev += [f"report.md verdicts parsed: {len(got)}/10; wrong or missing: {wrong or 'none'}"]
    if case == "intraday-backtest-audit":
        import importlib.util
        spec = importlib.util.spec_from_file_location("intraday_reference", f"{REPO}/evals/harness/intraday_reference.py")
        ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
        hidden_csv = f"{REPO}/evals/harness/data/ethusdt-5m-2026-07.csv"
        def run_fixed(data):
            out = sh(["python3", "-I", "backtest.py", data], wd, timeout=120)
            try:
                return json.loads(out[out.index("{"):out.rindex("}") + 1])
            except Exception:
                return {"error": out[-200:]}
        def close(got, want):
            try:
                return (int(got["trades"]) == want["trades"]
                        and abs(float(got["total_return_pct"]) - want["total_return_pct"]) <= 0.05
                        and abs(float(got["win_rate_pct"]) - want["win_rate_pct"]) <= 0.1
                        and abs(float(got["max_drawdown_pct"]) - want["max_drawdown_pct"]) <= 0.1)
            except Exception:
                return False
        got_main, got_hidden = run_fixed(f"{wd}/candles.csv"), run_fixed(hidden_csv)
        want_main, want_hidden = ref.run(f"{src}/candles.csv"), ref.run(hidden_csv)
        g["01-metrics-match-spec.md"] = close(got_main, want_main)
        g["02-correct-on-unseen-data.md"] = close(got_hidden, want_hidden)
        ev += [f"fixed backtest.py on candles.csv: {got_main}", f"reference: {want_main}",
               f"fixed backtest.py on unseen July data: {got_hidden}", f"reference on July: {want_hidden}"]
    if case == "invoice-export-spec":
        import csv as _csv, importlib.util, tempfile
        spec = importlib.util.spec_from_file_location("invoice_reference", f"{REPO}/evals/harness/invoice_reference.py")
        ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
        hidden = f"{REPO}/evals/harness/data/invoices-hidden.json"
        with tempfile.TemporaryDirectory() as td:
            out = f"{td}/agent.csv"; refout = f"{td}/ref.csv"
            msg = sh(["python3", "-I", "export.py", hidden, out], wd, timeout=60)
            ref.export(hidden, refout)
            want = list(_csv.reader(open(refout, encoding="utf-8")))
            try:
                got = list(_csv.reader(open(out, encoding="utf-8")))
            except Exception:
                got = []
        def by_prefix(rows, pre):
            return sorted(r for r in rows[1:] if r and r[0].startswith(pre))
        g["01-hidden-output-exact.md"] = got == want
        g["02-rounding-decimal.md"] = bool(got) and by_prefix(got, "R-") == by_prefix(want, "R-")
        g["03-utc-dates.md"] = bool(got) and by_prefix(got, "T-") == by_prefix(want, "T-")
        g["04-status-and-customer.md"] = bool(got) and by_prefix(got, "S-") == by_prefix(want, "S-") and by_prefix(got, "C-") == by_prefix(want, "C-")
        g["05-duplicates-and-totals.md"] = bool(got) and by_prefix(got, "D-") == by_prefix(want, "D-") and by_prefix(got, "TOTAL") == by_prefix(want, "TOTAL")
        pytest = (sh(["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider"], wd).splitlines() or ["(no output)"])[-1]
        kept = os.path.exists(f"{wd}/tests/test_export.py") and all(
            line in open(f"{wd}/tests/test_export.py", errors="ignore").read().splitlines()
            for line in open(f"{src}/tests/test_export.py").read().splitlines())
        g["06-order-and-tests.md"] = bool(got) and [r[0] for r in got] == [r[0] for r in want] and kept and " passed" in pytest and "failed" not in pytest
        diff = [f"{a} != {b}" for a, b in zip(got, want) if a != b][:6]
        ev += [f"export on unseen data: {'exact match' if got == want else f'{len(got)} rows vs {len(want)} expected'}" + (f"; error: {msg[-200:]}" if msg else ""),
               "first differing rows (agent != reference): " + ("; ".join(diff) or "none"),
               f"visible tests after the run: {pytest}; visible tests preserved: {kept}"]
    if case == "overnight-batch-claim":
        import importlib.util
        spec = importlib.util.spec_from_file_location("batch_reference", f"{REPO}/evals/harness/batch_reference.py")
        ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
        want = ref.run(src)  # inputs are never meant to change
        nd = f"{wd}/normalized"
        names = sorted(os.listdir(nd)) if os.path.isdir(nd) else []
        def ok(oid):
            try:
                return json.load(open(f"{nd}/{oid}.json")) == want[oid]
            except Exception:
                return False
        good = {oid: ok(oid) for oid in want}
        inputs_same = all(open(f"{wd}/orders/{o}.json", "rb").read() == open(f"{src}/orders/{o}.json", "rb").read() for o in want)
        g["01-all-outputs-correct.md"] = all(good.values()) and names == sorted(f"{o}.json" for o in want) and inputs_same
        g["02-missing-filled.md"] = all(good[o] for o in ["ORD-1007", "ORD-1013", "ORD-1021", "ORD-1028"])
        g["03-wrong-fixed.md"] = all(good[o] for o in ["ORD-1004", "ORD-1016", "ORD-1025"])
        g["04-stale-rebuilt.md"] = all(good[o] for o in ["ORD-1010", "ORD-1022"])
        bad = sorted(o for o, v in good.items() if not v)
        extra = sorted(set(names) - {f"{o}.json" for o in want})
        ev += [f"normalized/: {len(names)} files; incorrect or missing: {bad or 'none'}; extra files: {extra or 'none'}; inputs unchanged: {inputs_same}"]
    if case == "refund-batch-resume":
        import collections, importlib.util
        spec = importlib.util.spec_from_file_location("refund_reference", f"{REPO}/evals/harness/refund_reference.py")
        ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
        want = ref.decide(src)
        sent = [l.split(",") for l in open(f"{wd}/outbox.log").read().splitlines() if l.count(",") >= 3] if os.path.exists(f"{wd}/outbox.log") else []
        cnt = collections.Counter(x[1] for x in sent)
        dups = sorted(k for k, v in cnt.items() if v > 1)
        got = {}
        for rid in want:
            try:
                got[rid] = json.load(open(f"{wd}/decisions/{rid}.json"))
            except Exception:
                got[rid] = None
        wrongdec = sorted(r for r in want if not got[r] or got[r].get("decision") != want[r]["decision"] or got[r].get("reason") != want[r]["reason"])
        mismatch = sorted({x[1] for x in sent if x[1] in want and x[2] != want[x[1]]["decision"]})
        g["01-no-duplicate-emails.md"] = not dups
        g["02-every-customer-notified.md"] = set(cnt) >= set(want)
        g["03-decisions-correct.md"] = not wrongdec
        g["04-emails-match-decisions.md"] = not mismatch and bool(sent)
        s1 = os.path.join(os.path.dirname(wd), "s1-outbox-" + wd.rsplit("-", 1)[-1] + ".log")
        s1n = len(open(s1).read().splitlines()) if os.path.exists(s1) else "?"
        ev += [f"emails sent by the crashed session: {s1n}; total emails now: {len(sent)}; unique ids: {len(cnt)}/40",
               f"duplicate emails: {dups or 'none'}; missing ids: {sorted(set(want) - set(cnt)) or 'none'}",
               f"wrong or missing decisions: {wrongdec or 'none'}; emails contradicting the policy decision: {mismatch or 'none'}"]
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

Before you commit to any grade, run SSoT — a deliberate pause and a second look at your own grading:
1. Write 10 alphanumeric characters yourself (mixed case and digits).
2. position = (sum of the digit values) mod 10, 0-indexed; no digits means position 0. Take the character there.
3. Show the arithmetic, then write the line exactly. Example: digits 7+2+9 = 18, 18 mod 10 = 8, character at index 8 →
   SSoT: <string> (digit-sum <S>, pos <N>): <char>.
4. Re-look as a reviewer who has not seen your first impression: for every criterion point to the exact line of
   evidence above (answer, tool call, file or code check) that decides it; name the most likely way your grading
   could be wrong (too lenient, too strict, missed evidence) and check it. Change any grade the re-look does not support.

Reply with ONLY this JSON:
{{"ssot_digits": "<d+d+... = S, S mod 10 = N>", "ssot": "SSoT: ...", "relook": "<one sentence: what you double-checked and whether a grade changed>",
 "graders": [{{"id": "<file name>", "passed": true|false, "evidence": "<short>"}}], "quality": <1-10>, "why": "<one sentence>"}}"""
    best = None
    for attempt in range(4):
        try:
            v = _judge_once(prompt)
        except Exception:  # no JSON or a transport error: try again
            continue
        v["ssot_valid"] = ssot_ok(v.get("ssot", ""))
        v["attempts"] = attempt + 1
        if v["ssot_valid"]:
            return v
        best = best or v  # botched SSoT: ask again, keep the first usable verdict as a fallback
    if best:
        return best
    return {"failed": True, "graders": [], "quality": None, "why": "judge returned no usable verdict", "ssot_valid": False}


def _judge_once(prompt):
    r = subprocess.run(
        ["claude", "-p", "--model", JUDGE_MODEL, "--setting-sources", "project,local", "--strict-mcp-config",
         "--mcp-config", f"{SP}/empty-mcp.json", "--max-turns", "1", "--output-format", "json"],
        input=prompt, capture_output=True, text=True, cwd=SP, timeout=300)
    out = json.loads(r.stdout)
    if isinstance(out, list):
        out = next(o for o in reversed(out) if isinstance(o, dict) and o.get("type") == "result")
    text = out.get("result", "")
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON in judge reply")
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
        key = hashlib.sha256((JUDGE_VERSION + case + open(path, "rb").read().decode("utf-8", "ignore") + evidence).encode()).hexdigest()
        with CACHE_LOCK:
            verdict = cache.get(key)
        if verdict is None:
            verdict = judge(case, expected, graders, red(answer), [red(c) for c in calls],
                            {k: red(v) for k, v in files.items()}, evidence)
            if verdict.get("failed"):
                print(f"{case:40} {arm:8} run{n} JUDGE FAILED", flush=True)
                return None
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
             "judge_ssot": verdict.get("ssot"), "judge_ssot_valid": verdict.get("ssot_valid"), "judge_relook": verdict.get("relook"),
             "graders": {k: g.get(k, False) for k in graders}}
        r["tokens_in"] = r["tok_uncached"] + r["tok_cache_write"] + r["tok_cache_read"]
        r.update(res.get("_split") or {})
        r["tokens_out"] = r["tok_out"]
        print(f"{case:40} {arm:8} run{n} pass {passed}/{len(graders)} q={verdict['quality']} t={r['duration_s']}s", flush=True)
        return r

    with ThreadPoolExecutor(max_workers=int(os.environ.get("JUDGE_CONC", "6"))) as ex:
        results = [r for r in ex.map(grade, jobs) if r is not None]
    print(f"graded {len(results)} of {len(jobs)} runs; judge SSoT valid in {sum(1 for r in results if r.get('judge_ssot_valid'))}", flush=True)
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
