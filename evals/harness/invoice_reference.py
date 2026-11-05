"""Reference implementation of evals/invoice-export-spec/files/SPEC.md (used by the judge)."""
import csv
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

RATES = {"EUR": Decimal("0.21"), "GBP": Decimal("0.20"), "USD": Decimal("0")}
CENT = Decimal("0.01")


def q(x):
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def rows(invoices):
    last = {}
    for inv in invoices:
        last.pop(inv["id"], None)
        last[inv["id"]] = inv
    out = []
    for inv in last.values():
        if inv["status"] == "cancelled":
            continue
        net = q(sum((Decimal(str(l["qty"])) * Decimal(str(l["unit_price"])) for l in inv["lines"]), Decimal("0")))
        vat = q(net * RATES[inv["currency"]])
        gross = net + vat
        if inv["status"] == "refunded":
            net, vat, gross = -net, -vat, -gross
        day = datetime.fromisoformat(inv["issued_at"]).astimezone(timezone.utc).date().isoformat()
        cust = inv.get("customer")
        cust = cust if isinstance(cust, str) and cust.strip() else "UNKNOWN"
        out.append([inv["id"], cust, day, inv["currency"], net, vat, gross])
    out.sort(key=lambda r: (r[2], r[0]))
    tot = {}
    for r in out:
        t = tot.setdefault(r[3], [Decimal("0")] * 3)
        for i in range(3):
            t[i] += r[4 + i]
    out += [["TOTAL", "", "", c, *tot[c]] for c in sorted(tot)]
    return [[*r[:4], *(f"{v:.2f}" for v in r[4:])] for r in out]


def export(src, dst):
    with open(src, encoding="utf-8") as fh:
        data = json.load(fh)
    with open(dst, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["invoice_id", "customer", "issued_date", "currency", "net", "vat", "gross"])
        w.writerows(rows(data))


if __name__ == "__main__":
    export(sys.argv[1], sys.argv[2])
