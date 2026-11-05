#!/usr/bin/env python3
"""tgo — task-graph state machine the agent drives from the shell. Stdlib only.

The agent plans, the program enforces: a unit starts only when its dependencies are finished, becomes DONE only
when its check passes and a fresh SSoT re-look is recorded, a failed cause cannot be retried, the same failure twice
blocks the unit until a loop SSoT names a new cause, and `final` cannot claim "complete" with a required gap.
Every command appends to `.orchestration/<slug>.trace.jsonl`, so the replay page comes for free.

  tgo plan plan.json|-        validate and start a graph (goal, criteria, units with depends/criteria/check)
  tgo next                    what can run now
  tgo status                  every unit with its status
  tgo start U
  tgo done U --ssot S --angle A --note "..." [--check "cmd"]
  tgo fail U --sig "error signature" --cause "what this attempt tested"
  tgo ssot --trigger loop|commit|user --ssot S --note "..."
  tgo skip U --reason optional|superseded [--by "..."]
  tgo replan --reason "..." [--add JSON] [--remove U ...] [--stale U ...]
  tgo final --ssot S --angle A --note "..."
  tgo render                  write the replay page and print its link

Env: TGO_SSOT=0 turns the SSoT requirement off; TGO_SSOT_HISTORY overrides the string-history file.
"""
import argparse
import json
import os
import re
import subprocess
import sys

DIR = ".orchestration"
ANGLES = ["user", "spec", "edge", "reviewer", "next"]
ANGLE_Q = {
    "user": "Would the person who asked accept this as done? Name the evidence they would look at.",
    "spec": "Which requirement is not covered by the evidence? Name the requirement and the proof it is met.",
    "edge": "Which input breaks it — empty, zero, max, duplicate, timezone, unicode, failure? Name the case you checked.",
    "reviewer": "What is the most likely way this is wrong? Name it and the check that rules it out.",
    "next": "Could someone else continue from the artifacts alone? Name the file or command they would use.",
}
FINISHED = {"DONE", "SKIPPED"}
# Example strings printed in this skill's own docs: copying one is the opposite of a fresh pause.
DOC_EXAMPLES = ["Tq3vR8m1Kx", "hN5r2KpW0e", "Kd3m9Vw1Lp", "Rb7xQ2mT4z"]


def die(msg, code=2):
    print(msg)
    sys.exit(code)


# --- storage -----------------------------------------------------------------

def slug_file():
    return os.path.join(DIR, "CURRENT")


def paths():
    if not os.path.exists(slug_file()):
        die("No graph yet: run `tgo plan plan.json` first.")
    slug = open(slug_file()).read().strip()
    return os.path.join(DIR, f"{slug}.state.json"), os.path.join(DIR, f"{slug}.trace.jsonl")


def load():
    sp, _ = paths()
    with open(sp) as fh:
        return json.load(fh)


def save(st):
    sp, _ = paths()
    tmp = sp + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(st, fh, indent=1)
    os.replace(tmp, sp)


def emit(st, *events):
    _, tp = paths()
    with open(tp, "a") as fh:
        for e in events:
            st["seq"] += 1
            fh.write(json.dumps({"seq": st["seq"], **e}, ensure_ascii=False) + "\n")


def history_path():
    return os.environ.get("TGO_SSOT_HISTORY") or os.path.join(os.path.expanduser("~"), ".cache", "task-graph-orchestration", "ssot-history")


# --- SSoT --------------------------------------------------------------------

def ssot_parts(s):
    pos = sum(int(c) for c in s if c.isdigit()) % 10
    return pos, s[pos]


def check_ssot(st, s, angle=None):
    """Validate a fresh SSoT string; return (line, angle). Exits on any problem."""
    if not re.fullmatch(r"[A-Za-z0-9]{10}", s or ""):
        die("SSoT string must be exactly 10 letters/digits you write yourself.")
    if sum(c.isdigit() for c in s) < 2 or not any(c.isupper() for c in s) or not any(c.islower() for c in s) or len(set(s)) < 7:
        die("SSoT string needs upper and lower case letters, at least 2 digits and at least 7 distinct characters. Write a new one.")
    seen = DOC_EXAMPLES + list(st.get("ssot_strings", []))
    hp = history_path()
    if os.path.exists(hp):
        seen += open(hp).read().split()
    for old in seen:
        if old == s:
            die(f"SSoT string {s} was already used. Write a fresh one — a remembered string gives no pause.")
        if len(old) == 10 and sum(a == b for a, b in zip(old, s)) >= 7:
            die(f"SSoT string {s} is a template of {old} (same skeleton). Write a genuinely new one.")
    pos, ch = ssot_parts(s)
    want = ANGLES[pos % 5]
    if angle is not None and angle != want:
        die(f"Wrong angle: digit-sum position {pos} gives angle '{want}' ({ANGLE_Q[want]})")
    st.setdefault("ssot_strings", []).append(s)
    try:
        os.makedirs(os.path.dirname(hp), exist_ok=True)
        with open(hp, "a") as fh:
            fh.write(s + "\n")
    except OSError:
        pass
    digits = sum(int(c) for c in s if c.isdigit())
    return f"SSoT: {s} (digit-sum {digits}, pos {pos}): {ch}.", want


def check_note(note):
    if not note or len(note.strip()) < 40 or not re.search(r"[0-9/`.:]", note):
        die("The re-look note must answer the angle concretely (40+ characters, citing a file, test, command, line or number).")


def ssot_on():
    return os.environ.get("TGO_SSOT", "1") != "0"


# --- graph helpers -----------------------------------------------------------

def find_cycle(units):
    graph = {u["id"]: list(u.get("depends", [])) for u in units}
    state = {}

    def visit(n):
        state[n] = 1
        for m in graph.get(n, []):
            if state.get(m) == 1 or (state.get(m) is None and visit(m)):
                return True
        state[n] = 2
        return False

    return any(state.get(n) is None and visit(n) for n in graph)


def validate(units, criteria, existing=()):
    ids = [u.get("id") for u in units]
    known = set(ids) | set(existing)
    if len(set(ids)) != len(ids) or any(not i for i in ids) or set(ids) & set(existing):
        die("Unit ids must be present and unique.")
    for u in units:
        for d in u.get("depends", []):
            if d not in known:
                die(f"{u['id']} depends on unknown unit {d}.")
        if not u.get("check"):
            die(f"{u['id']} has no check: give a shell command that passes only when the unit is right.")
        for c in u.get("criteria", []):
            if c not in criteria:
                die(f"{u['id']} refers to unknown criterion {c}.")


def ready(st):
    out = []
    for uid, u in st["units"].items():
        if u["status"] in ("READY", "STALE") and all(st["units"][d]["status"] in FINISHED for d in u["depends"]):
            out.append(uid)
    return out


def unit(st, uid):
    if uid not in st["units"]:
        die(f"Unknown unit {uid}.")
    return st["units"][uid]


def set_status(st, uid, to):
    st["units"][uid]["status"] = to
    emit(st, {"ev": "status", "unit": uid, "to": to})


def summary(st):
    left = [u for u, x in st["units"].items() if x["status"] not in FINISHED]
    return f"READY: {', '.join(ready(st)) or '-'}   open: {', '.join(left) or 'none — run tgo final'}"


# --- commands ----------------------------------------------------------------

def cmd_plan(a):
    data = json.load(sys.stdin if a.file == "-" else open(a.file))
    crit = {c["id"]: c for c in data.get("criteria", [])}
    units = data.get("units", [])
    if not data.get("goal") or not crit or not units:
        die("A plan needs goal, criteria and units.")
    validate(units, crit)
    if find_cycle(units):
        die("The dependency graph has a cycle.")
    covered = {c for u in units for c in u.get("criteria", [])}
    gaps = [c for c, v in crit.items() if v.get("required", True) and c not in covered]
    if gaps:
        die(f"Required criteria not covered by any unit: {', '.join(gaps)}.")
    os.makedirs(DIR, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", data["goal"].lower()).strip("-")[:40] or "goal"
    with open(slug_file(), "w") as fh:
        fh.write(slug)
    st = {"seq": 0, "goal": data["goal"], "criteria": crit,
          "units": {u["id"]: {"title": u.get("title", ""), "depends": u.get("depends", []), "criteria": u.get("criteria", []),
                              "check": u["check"], "effect": u.get("effect", "reversible"), "status": "READY",
                              "causes": [], "sigs": [], "blocked_loop": False} for u in units}}
    open(paths()[1], "w").close()
    emit(st, {"ev": "plan", "mode": data.get("mode", "FULL"), "goal": data["goal"], "criteria": list(crit.values()),
              "units": [{k: u.get(k) for k in ("id", "title", "depends", "criteria", "effect")} for u in units]})
    save(st)
    print(f"Plan accepted: {len(units)} units, {len(crit)} criteria.\n{summary(st)}")


def cmd_next(a):
    st = load()
    print(summary(st))


def cmd_status(a):
    st = load()
    for uid, u in st["units"].items():
        print(f"{uid:6} {u['status']:9} {u['title']}" + (f"  (tested: {'; '.join(u['causes'])})" if u["causes"] else ""))
    print(summary(st))


def cmd_start(a):
    st = load()
    u = unit(st, a.unit)
    if u["blocked_loop"]:
        die(f"{a.unit} failed twice with the same signature. Run a loop SSoT first: "
            f"tgo ssot --trigger loop --ssot <fresh string> --note \"shared assumption: ...; new cause: ...\"")
    missing = [d for d in u["depends"] if st["units"][d]["status"] not in FINISHED]
    if missing:
        die(f"{a.unit} waits for {', '.join(missing)}.")
    if u["status"] in FINISHED:
        die(f"{a.unit} is already {u['status']}.")
    set_status(st, a.unit, "RUNNING")
    save(st)
    print(f"{a.unit} RUNNING. When it is right: tgo done {a.unit} (runs its check: {u['check']})")


def run_check(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=float(os.environ.get("TGO_CHECK_TIMEOUT", "600")))
    out = (r.stdout + r.stderr).strip()
    return r.returncode, out


def record_failure(st, uid, sig, cause):
    u = st["units"][uid]
    norm = cause.strip().lower()
    if norm in u["causes"]:
        die(f"Cause '{cause}' was already tested on {uid}. Name a different cause (tested: {'; '.join(u['causes'])}).")
    loop = bool(u["sigs"]) and u["sigs"][-1] == sig
    u["causes"].append(norm)
    u["sigs"].append(sig)
    emit(st, {"ev": "failure", "unit": uid, "signature": sig[:160], "cause": cause[:160]})
    set_status(st, uid, "REPAIR")
    if loop:
        u["blocked_loop"] = True
        print(f"LOOP: {uid} failed twice with '{sig[:100]}'. Attempts so far: {'; '.join(u['causes'])}.\n"
              f"Before the next attempt run a loop SSoT: name the assumption all attempts share, then a new cause or strategy.")


def cmd_done(a):
    st = load()
    u = unit(st, a.unit)
    if u["status"] not in ("RUNNING", "REPAIR", "VERIFYING"):
        die(f"{a.unit} is {u['status']}; start it first.")
    line = angle = None
    if ssot_on():
        if not a.ssot or not a.angle:
            die("DONE needs a fresh SSoT re-look: --ssot <10 chars you write> --angle <angle from its position> --note \"...\".\n"
                "Angle = ['user','spec','edge','reviewer','next'][(digit-sum mod 10) mod 5].")
        line, angle = check_ssot(st, a.ssot, a.angle)
    check_note(a.note)
    cmd = a.check or u["check"]
    set_status(st, a.unit, "VERIFYING")
    code, out = run_check(cmd)
    if code != 0:
        sig = (out.splitlines() or [f"exit {code}"])[-1][:160]
        record_failure(st, a.unit, sig, a.cause or f"attempt {len(u['causes']) + 1}")
        save(st)
        die(f"Check failed (exit {code}): {cmd}\n{out[-1500:]}\n{a.unit} -> REPAIR. Fix the smallest responsible part, then tgo done again.", 1)
    for c in u["criteria"] or [None]:
        ev = {"ev": "evidence", "unit": a.unit, "kind": "command", "ref": f"{cmd} -> exit 0"}
        if c:
            ev["criterion"] = c
        emit(st, ev)
    if line:
        emit(st, {"ev": "ssot", "trigger": "done", "unit": a.unit, "angle": angle, "line": line, "outcome": a.note[:300]})
    set_status(st, a.unit, "DONE")
    u["blocked_loop"] = False
    emit(st, {"ev": "checkpoint", "after": a.unit, "decision": "continue", "reason": "check passed"})
    save(st)
    print(f"{a.unit} DONE. {summary(st)}\nCheckpoint: if the goal is already met, skip the rest (tgo skip U --reason superseded) and run tgo final.")


def cmd_fail(a):
    st = load()
    unit(st, a.unit)
    record_failure(st, a.unit, a.sig, a.cause)
    save(st)
    print(f"{a.unit} -> REPAIR. {summary(st)}")


def cmd_ssot(a):
    st = load()
    line, _ = check_ssot(st, a.ssot)
    check_note(a.note)
    emit(st, {"ev": "ssot", "trigger": a.trigger, "line": line, "outcome": a.note[:300]})
    if a.trigger == "loop":
        for u in st["units"].values():
            u["blocked_loop"] = False
    save(st)
    print(line)


def cmd_skip(a):
    st = load()
    u = unit(st, a.unit)
    if a.reason not in ("optional", "superseded"):
        die("skip needs --reason optional|superseded.")
    if a.reason == "optional" and any(st["criteria"][c].get("required", True) for c in u["criteria"]
                                      if not any(o["status"] == "DONE" and c in o["criteria"] for o in st["units"].values())):
        die(f"{a.unit} carries a required criterion nobody else has met; skipping it makes the result incomplete.")
    emit(st, {"ev": "skip", "unit": a.unit, "reason": a.reason, "by": a.by or ""})
    st["units"][a.unit]["status"] = "SKIPPED"
    save(st)
    print(f"{a.unit} SKIPPED ({a.reason}). {summary(st)}")


def cmd_replan(a):
    st = load()
    add = json.loads(a.add) if a.add else []
    validate(add, st["criteria"], existing=st["units"].keys())
    allu = [{"id": k, "depends": v["depends"]} for k, v in st["units"].items() if k not in (a.remove or [])] + add
    if find_cycle(allu):
        die("The new graph has a cycle.")
    for uid in a.remove or []:
        unit(st, uid)
        del st["units"][uid]
    for u in add:
        st["units"][u["id"]] = {"title": u.get("title", ""), "depends": u.get("depends", []), "criteria": u.get("criteria", []),
                                "check": u["check"], "effect": u.get("effect", "reversible"), "status": "READY",
                                "causes": [], "sigs": [], "blocked_loop": False}
    for uid in a.stale or []:
        unit(st, uid)["status"] = "STALE"
    emit(st, {"ev": "replan", "reason": a.reason,
              "add": [{k: u.get(k) for k in ("id", "title", "depends", "criteria", "cause")} for u in add],
              "remove": a.remove or [], "stale": a.stale or []})
    save(st)
    print(f"Replanned. {summary(st)}")


def cmd_final(a):
    st = load()
    line = angle = None
    if ssot_on():
        if not a.ssot or not a.angle:
            die("final needs a fresh SSoT re-look: --ssot, --angle and --note.")
        line, angle = check_ssot(st, a.ssot, a.angle)
    check_note(a.note)
    met = {c for u in st["units"].values() if u["status"] == "DONE" for c in u["criteria"]}
    gaps = [f"{c}: no passing unit" for c, v in st["criteria"].items() if v.get("required", True) and c not in met]
    open_units = [u for u, x in st["units"].items() if x["status"] not in FINISHED]
    gaps += [f"{u}: still {st['units'][u]['status']}" for u in open_units]
    if line:
        emit(st, {"ev": "ssot", "trigger": "final", "angle": angle, "line": line, "outcome": a.note[:300]})
    emit(st, {"ev": "final", "result": "incomplete" if gaps else "complete", "gaps": gaps})
    save(st)
    if gaps:
        die("INCOMPLETE — report these gaps instead of claiming success:\n- " + "\n- ".join(gaps), 1)
    print("COMPLETE: every required criterion has a passing check.")


def cmd_render(a):
    _, tp = paths()
    here = os.path.dirname(os.path.abspath(__file__))
    r = subprocess.run([sys.executable, os.path.join(here, "trace_graph.py"), "render", os.path.abspath(tp)], capture_output=True, text=True)
    print((r.stdout + r.stderr).strip())


def main(argv=None):
    p = argparse.ArgumentParser(prog="tgo", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("plan"); s.add_argument("file"); s.set_defaults(f=cmd_plan)
    sub.add_parser("next").set_defaults(f=cmd_next)
    sub.add_parser("status").set_defaults(f=cmd_status)
    s = sub.add_parser("start"); s.add_argument("unit"); s.set_defaults(f=cmd_start)
    s = sub.add_parser("done"); s.add_argument("unit"); s.add_argument("--ssot"); s.add_argument("--angle", choices=ANGLES)
    s.add_argument("--note", required=True); s.add_argument("--check"); s.add_argument("--cause"); s.set_defaults(f=cmd_done)
    s = sub.add_parser("fail"); s.add_argument("unit"); s.add_argument("--sig", required=True); s.add_argument("--cause", required=True)
    s.set_defaults(f=cmd_fail)
    s = sub.add_parser("ssot"); s.add_argument("--trigger", choices=["loop", "commit", "user"], required=True)
    s.add_argument("--ssot", required=True); s.add_argument("--note", required=True); s.set_defaults(f=cmd_ssot)
    s = sub.add_parser("skip"); s.add_argument("unit"); s.add_argument("--reason"); s.add_argument("--by"); s.set_defaults(f=cmd_skip)
    s = sub.add_parser("replan"); s.add_argument("--reason", required=True); s.add_argument("--add")
    s.add_argument("--remove", nargs="*"); s.add_argument("--stale", nargs="*"); s.set_defaults(f=cmd_replan)
    s = sub.add_parser("final"); s.add_argument("--ssot"); s.add_argument("--angle", choices=ANGLES); s.add_argument("--note", required=True)
    s.set_defaults(f=cmd_final)
    sub.add_parser("render").set_defaults(f=cmd_render)
    a = p.parse_args(argv)
    a.f(a)


if __name__ == "__main__":
    main()
