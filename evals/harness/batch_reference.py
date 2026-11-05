"""Reference normaliser for evals/overnight-batch-claim/files/RULES.md (used by the generator and the judge)."""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal

COUNTRY = {"netherlands": "NL", "germany": "DE", "united kingdom": "GB", "great britain": "GB",
           "france": "FR", "belgium": "BE", "spain": "ES", "poland": "PL"}


def normalise(raw_bytes):
    o = json.loads(raw_bytes)
    items = sorted(({"sku": i["sku"], "qty": int(i["qty"]), "unit_cents": int(Decimal(str(i["price"])) * 100)} for i in o["items"]),
                   key=lambda i: i["sku"])
    return {"order_id": o["order_id"], "email": o["email"].strip().lower(), "country": COUNTRY[o["country"].strip().lower()],
            "total_cents": sum(i["qty"] * i["unit_cents"] for i in items), "items": items,
            "created_utc": datetime.fromisoformat(o["created_at"]).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_sha256": hashlib.sha256(raw_bytes).hexdigest()}


def run(root):
    return {f[:-5]: normalise(open(os.path.join(root, "orders", f), "rb").read())
            for f in sorted(os.listdir(os.path.join(root, "orders"))) if f.endswith(".json")}


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1]), indent=1))
