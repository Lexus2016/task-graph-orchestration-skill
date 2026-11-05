"""Reference decisions for evals/refund-batch-resume (POLICY.md)."""
import csv, json, os
from datetime import date


def decide(root):
    refunded = {r["order_id"] for r in csv.DictReader(open(os.path.join(root, "ledger.csv")))}
    out = {}
    for f in sorted(os.listdir(os.path.join(root, "refunds"))):
        r = json.load(open(os.path.join(root, "refunds", f)))
        days = (date.fromisoformat(r["request_date"]) - date.fromisoformat(r["order_date"])).days
        reason = "too_late" if days > 30 else "over_limit" if r["amount_eur"] > 200 else "already_refunded" if r["order_id"] in refunded else "ok"
        out[r["id"]] = {"id": r["id"], "decision": "approved" if reason == "ok" else "rejected", "reason": reason}
    return out
