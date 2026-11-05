"""Tests for skills/task-graph-orchestration/scripts/tgo.py. Run: python3 -m pytest -q tests"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TGO = os.path.join(HERE, "..", "skills", "task-graph-orchestration", "scripts", "tgo.py")

PLAN = {
    "goal": "fix the exporter",
    "criteria": [{"id": "c1", "text": "tests pass", "required": True},
                 {"id": "c2", "text": "docs updated", "required": False}],
    "units": [
        {"id": "u1", "title": "fix code", "depends": [], "criteria": ["c1"], "check": "true", "effect": "reversible"},
        {"id": "u2", "title": "update docs", "depends": ["u1"], "criteria": ["c2"], "check": "true"},
    ],
}


def tgo(tmp_path, *args, stdin=None, env=None):
    e = dict(os.environ, TGO_SSOT_HISTORY=str(tmp_path / "ssot-history"))
    e.update(env or {})
    r = subprocess.run([sys.executable, TGO, *args], cwd=tmp_path, input=stdin, capture_output=True, text=True, env=e)
    return r.returncode, r.stdout + r.stderr


def plan(tmp_path, p=PLAN):
    code, out = tgo(tmp_path, "plan", "-", stdin=json.dumps(p))
    assert code == 0, out


def trace(tmp_path):
    files = [f for f in os.listdir(tmp_path / ".orchestration") if f.endswith(".trace.jsonl")]
    return [json.loads(l) for l in open(tmp_path / ".orchestration" / files[0])]


def angle_for(s):
    pos = sum(int(c) for c in s if c.isdigit()) % 10
    return ["user", "spec", "edge", "reviewer", "next"][pos % 5]


NOTE = "edge: empty input handled, see tests/test_export.py::test_empty (1 passed)"


# --- plan validation ---------------------------------------------------------

def test_plan_rejects_cycle(tmp_path):
    p = json.loads(json.dumps(PLAN))
    p["units"][0]["depends"] = ["u2"]
    code, out = tgo(tmp_path, "plan", "-", stdin=json.dumps(p))
    assert code != 0 and "cycle" in out.lower()


def test_plan_rejects_uncovered_required_criterion(tmp_path):
    p = json.loads(json.dumps(PLAN))
    p["units"][0]["criteria"] = []
    code, out = tgo(tmp_path, "plan", "-", stdin=json.dumps(p))
    assert code != 0 and "c1" in out


def test_plan_writes_trace_and_next_lists_ready(tmp_path):
    plan(tmp_path)
    assert trace(tmp_path)[0]["ev"] == "plan"
    code, out = tgo(tmp_path, "next")
    ready_part = out.split("READY:")[1].split("open:")[0]
    assert code == 0 and "u1" in ready_part and "u2" not in ready_part


# --- transitions -------------------------------------------------------------

def test_start_refuses_unmet_dependency(tmp_path):
    plan(tmp_path)
    code, out = tgo(tmp_path, "start", "u2")
    assert code != 0 and "u1" in out


def test_done_requires_passing_check(tmp_path):
    p = json.loads(json.dumps(PLAN))
    p["units"][0]["check"] = "false"
    plan(tmp_path, p)
    tgo(tmp_path, "start", "u1")
    s = "Kq7Rm2Xb9t"
    code, out = tgo(tmp_path, "done", "u1", "--ssot", s, "--angle", angle_for(s), "--note", NOTE)
    assert code != 0 and "REPAIR" in out
    ev = trace(tmp_path)
    assert any(e["ev"] == "failure" and e["unit"] == "u1" for e in ev)
    assert not any(e["ev"] == "status" and e.get("to") == "DONE" for e in ev)


def test_done_happy_path_records_evidence_ssot_and_checkpoint(tmp_path):
    plan(tmp_path)
    tgo(tmp_path, "start", "u1")
    s = "Kq7Rm2Xb9t"
    code, out = tgo(tmp_path, "done", "u1", "--ssot", s, "--angle", angle_for(s), "--note", NOTE)
    assert code == 0, out
    kinds = [e["ev"] for e in trace(tmp_path)]
    i_ev, i_done = kinds.index("evidence"), max(i for i, e in enumerate(trace(tmp_path)) if e.get("to") == "DONE")
    assert i_ev < i_done and "ssot" in kinds and kinds[-1] == "checkpoint"


# --- SSoT on DONE ------------------------------------------------------------

def test_done_rejects_wrong_angle(tmp_path):
    plan(tmp_path)
    tgo(tmp_path, "start", "u1")
    s = "Kq7Rm2Xb9t"
    wrong = next(a for a in ["user", "spec", "edge", "reviewer", "next"] if a != angle_for(s))
    code, out = tgo(tmp_path, "done", "u1", "--ssot", s, "--angle", wrong, "--note", NOTE)
    assert code != 0 and angle_for(s) in out


def test_done_rejects_reused_and_template_strings(tmp_path):
    p = json.loads(json.dumps(PLAN))
    p["units"][1]["depends"] = []
    plan(tmp_path, p)
    for u in ("u1", "u2"):
        tgo(tmp_path, "start", u)
    s = "Kq7Rm2Xb9t"
    assert tgo(tmp_path, "done", "u1", "--ssot", s, "--angle", angle_for(s), "--note", NOTE)[0] == 0
    code, out = tgo(tmp_path, "done", "u2", "--ssot", s, "--angle", angle_for(s), "--note", NOTE)
    assert code != 0 and "used" in out.lower()
    near = "Kq7Rm2Xb9z"  # 9 of 10 positions identical: a template, not a fresh string
    code, out = tgo(tmp_path, "done", "u2", "--ssot", near, "--angle", angle_for(near), "--note", NOTE)
    assert code != 0 and "template" in out.lower()


def test_done_rejects_malformed_string(tmp_path):
    plan(tmp_path)
    tgo(tmp_path, "start", "u1")
    for bad in ("abcdefghij", "ABC123", "aaaaaaaaa1"):
        assert tgo(tmp_path, "done", "u1", "--ssot", bad, "--angle", angle_for(bad), "--note", NOTE)[0] != 0


def test_done_rejects_empty_note(tmp_path):
    plan(tmp_path)
    tgo(tmp_path, "start", "u1")
    s = "Kq7Rm2Xb9t"
    code, out = tgo(tmp_path, "done", "u1", "--ssot", s, "--angle", angle_for(s), "--note", "looks fine")
    assert code != 0


# --- failure memory and loops ------------------------------------------------

def test_fail_rejects_repeated_cause(tmp_path):
    plan(tmp_path)
    tgo(tmp_path, "start", "u1")
    assert tgo(tmp_path, "fail", "u1", "--sig", "KeyError: x", "--cause", "key names")[0] == 0
    code, out = tgo(tmp_path, "fail", "u1", "--sig", "KeyError: y", "--cause", "Key Names")
    assert code != 0 and "already tested" in out


def test_same_signature_twice_blocks_until_loop_ssot(tmp_path):
    plan(tmp_path)
    tgo(tmp_path, "start", "u1")
    tgo(tmp_path, "fail", "u1", "--sig", "KeyError: db.url", "--cause", "key names")
    code, out = tgo(tmp_path, "fail", "u1", "--sig", "KeyError: db.url", "--cause", "loader path")
    assert "loop" in out.lower()
    code, out = tgo(tmp_path, "start", "u1")
    assert code != 0 and "ssot" in out.lower()
    s = "Pw4Lc8Hn1e"
    code, out = tgo(tmp_path, "ssot", "--trigger", "loop", "--ssot", s, "--note",
                    "shared assumption: the service reads the standard loader; new cause: env override in deploy.yaml")
    assert code == 0, out
    assert tgo(tmp_path, "start", "u1")[0] == 0


# --- skip, replan, final -----------------------------------------------------

def test_skip_requires_reason_and_unblocks_dependents(tmp_path):
    p = json.loads(json.dumps(PLAN))
    p["units"].append({"id": "u3", "title": "release", "depends": ["u2"], "criteria": [], "check": "true"})
    plan(tmp_path, p)
    assert tgo(tmp_path, "skip", "u2")[0] != 0
    assert tgo(tmp_path, "skip", "u2", "--reason", "optional")[0] == 0
    tgo(tmp_path, "start", "u1")
    s = "Kq7Rm2Xb9t"
    tgo(tmp_path, "done", "u1", "--ssot", s, "--angle", angle_for(s), "--note", NOTE)
    assert "u3" in tgo(tmp_path, "next")[1]


def test_replan_adds_units_and_marks_stale(tmp_path):
    plan(tmp_path)
    tgo(tmp_path, "start", "u1")
    s = "Kq7Rm2Xb9t"
    tgo(tmp_path, "done", "u1", "--ssot", s, "--angle", angle_for(s), "--note", NOTE)
    add = json.dumps([{"id": "u4", "title": "fix rounding", "depends": [], "criteria": ["c1"], "check": "true"}])
    code, out = tgo(tmp_path, "replan", "--reason", "rounding bug found", "--add", add, "--stale", "u1")
    assert code == 0, out
    st = tgo(tmp_path, "status")[1]
    assert "u1" in st and "STALE" in st and "u4" in st


def test_final_refuses_complete_with_required_gap(tmp_path):
    plan(tmp_path)
    s = "Zt3Vb6Qm0r"
    code, out = tgo(tmp_path, "final", "--ssot", s, "--angle", angle_for(s), "--note", NOTE)
    assert code != 0 and "c1" in out
    assert trace(tmp_path)[-1]["ev"] == "final" and trace(tmp_path)[-1]["result"] == "incomplete"


def test_final_complete_when_required_done(tmp_path):
    plan(tmp_path)
    tgo(tmp_path, "start", "u1")
    s = "Kq7Rm2Xb9t"
    tgo(tmp_path, "done", "u1", "--ssot", s, "--angle", angle_for(s), "--note", NOTE)
    tgo(tmp_path, "skip", "u2", "--reason", "optional")
    s2 = "Zt3Vb6Qm0r"
    code, out = tgo(tmp_path, "final", "--ssot", s2, "--angle", angle_for(s2), "--note", NOTE)
    assert code == 0, out
    assert trace(tmp_path)[-1] == {**trace(tmp_path)[-1], "ev": "final", "result": "complete"}


def test_no_ssot_mode_skips_ssot(tmp_path):
    plan(tmp_path)
    tgo(tmp_path, "start", "u1")
    code, out = tgo(tmp_path, "done", "u1", "--note", NOTE, env={"TGO_SSOT": "0"})
    assert code == 0, out
    assert not any(e["ev"] == "ssot" for e in trace(tmp_path))


def test_trace_is_valid_for_trace_graph(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "trace_graph", os.path.join(HERE, "..", "skills", "task-graph-orchestration", "scripts", "trace_graph.py"))
    tg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tg)
    plan(tmp_path)
    tgo(tmp_path, "start", "u1")
    s = "Kq7Rm2Xb9t"
    tgo(tmp_path, "done", "u1", "--ssot", s, "--angle", angle_for(s), "--note", NOTE)
    tgo(tmp_path, "skip", "u2", "--reason", "optional")
    s2 = "Zt3Vb6Qm0r"
    tgo(tmp_path, "final", "--ssot", s2, "--angle", angle_for(s2), "--note", NOTE)
    errors = [f for f in tg.check(trace(tmp_path), []) if f["severity"] == "error"]
    assert errors == []


def test_done_rejects_skill_doc_example(tmp_path):
    plan(tmp_path)
    tgo(tmp_path, "start", "u1")
    s = "Tq3vR8m1Kx"  # printed in SKILL.md as the example
    code, out = tgo(tmp_path, "done", "u1", "--ssot", s, "--angle", angle_for(s), "--note", NOTE)
    assert code != 0 and "used" in out.lower()
