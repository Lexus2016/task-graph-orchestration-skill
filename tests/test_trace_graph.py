"""Tests for skills/task-graph-orchestration/scripts/trace_graph.py checks. Run: python3 -m pytest -q tests"""
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = importlib.util.spec_from_file_location(
    "trace_graph", os.path.join(HERE, "..", "skills", "task-graph-orchestration", "scripts", "trace_graph.py"))
tg = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tg)

PLAN = {"seq": 1, "ev": "plan", "mode": "LITE", "goal": "g",
        "criteria": [{"id": "c1", "text": "fixed", "required": True}],
        "units": [{"id": "u1", "title": "fix", "depends": [], "criteria": ["c1"]}]}


def codes(events):
    for i, e in enumerate(events, 1):
        e.setdefault("seq", i)
    return {f["code"] for f in tg.check(events, [])}


def tail(seq):
    return [{"seq": seq, "ev": "evidence", "unit": "u1", "criterion": "c1", "kind": "test", "ref": "pytest ok"},
            {"seq": seq + 1, "ev": "status", "unit": "u1", "to": "DONE"},
            {"seq": seq + 2, "ev": "checkpoint", "after": "u1", "decision": "stop"},
            {"seq": seq + 3, "ev": "ssot", "trigger": "final", "line": "SSoT: x", "outcome": "ok"},
            {"seq": seq + 4, "ev": "final", "result": "complete", "gaps": []}]


def test_clean_trace_has_no_findings():
    ev = [dict(PLAN), {"seq": 2, "ev": "status", "unit": "u1", "to": "RUNNING"}] + tail(3)
    assert codes(ev) == set()


def test_done_without_evidence_is_an_error():
    ev = [dict(PLAN), {"seq": 2, "ev": "status", "unit": "u1", "to": "RUNNING"},
          {"seq": 3, "ev": "status", "unit": "u1", "to": "DONE"}]
    assert "done-without-evidence" in codes(ev)


def test_replan_counts_as_checkpoint():
    ev = [dict(PLAN), {"seq": 2, "ev": "status", "unit": "u1", "to": "RUNNING"},
          {"seq": 3, "ev": "status", "unit": "u1", "to": "FAILED"},
          {"seq": 4, "ev": "replan", "reason": "r", "add": [{"id": "u2", "title": "b", "depends": []}]},
          {"seq": 5, "ev": "status", "unit": "u2", "to": "RUNNING"}]
    assert "no-checkpoint" not in codes(ev)


def failure(seq, cause, sig="KeyError: db.url"):
    return {"seq": seq, "ev": "failure", "unit": "u1", "signature": sig, "cause": cause, "next": "try other"}


def test_same_cause_tested_twice_is_flagged():
    ev = [dict(PLAN), {"seq": 2, "ev": "status", "unit": "u1", "to": "RUNNING"},
          failure(3, "v2 key names"), {"seq": 4, "ev": "ssot", "trigger": "loop", "line": "SSoT: x", "outcome": "o"},
          failure(5, "V2 key names ")]
    assert "repeated-cause" in codes(ev)


def test_different_causes_are_fine():
    ev = [dict(PLAN), {"seq": 2, "ev": "status", "unit": "u1", "to": "RUNNING"},
          failure(3, "v2 key names"), {"seq": 4, "ev": "ssot", "trigger": "loop", "line": "SSoT: x", "outcome": "o"},
          failure(5, "custom loader bypasses shim")] + tail(6)
    assert codes(ev) == set()


def test_same_signature_twice_without_loop_ssot_is_flagged():
    ev = [dict(PLAN), {"seq": 2, "ev": "status", "unit": "u1", "to": "RUNNING"},
          failure(3, "v2 key names"), failure(4, "nested format")]
    assert "loop-without-ssot" in codes(ev)


def test_loop_ssot_between_repeats_clears_the_flag():
    ev = [dict(PLAN), {"seq": 2, "ev": "status", "unit": "u1", "to": "RUNNING"},
          failure(3, "v2 key names"), {"seq": 4, "ev": "ssot", "trigger": "loop", "line": "SSoT: x", "outcome": "o"},
          failure(5, "nested format")]
    assert "loop-without-ssot" not in codes(ev)


def test_replan_back_to_a_failed_unit_shape_is_flagged():
    ev = [dict(PLAN), {"seq": 2, "ev": "status", "unit": "u1", "to": "RUNNING"},
          failure(3, "v2 key names"), {"seq": 4, "ev": "status", "unit": "u1", "to": "FAILED"},
          {"seq": 5, "ev": "replan", "reason": "retry", "add": [{"id": "u2", "title": "fix", "depends": [], "cause": "v2 key names"}]}]
    assert "repeated-cause" in codes(ev)


def test_render_writes_a_self_contained_page(tmp_path):
    trace = tmp_path / "goal.trace.jsonl"
    ev = [dict(PLAN), {"seq": 2, "ev": "status", "unit": "u1", "to": "RUNNING"}, failure(3, "v2 key names")] + tail(4)
    trace.write_text("\n".join(json.dumps(e) for e in ev) + "\n")
    url, run = tg.render(str(trace))
    page = (tmp_path / "goal.graph.html").read_text()
    assert url == "file://" + str(tmp_path / "goal.graph.html")
    assert "/*__BUNDLE__*/null" not in page and '"ev": "failure"' in page
    assert "<script src=" not in page  # no external dependencies
