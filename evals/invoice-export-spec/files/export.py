"""Invoice export for the accounting import. See SPEC.md. Usage: python3 export.py invoices.json out.csv"""
import csv
import json
import sys

VAT = {"EUR": 0.21, "GBP": 0.20, "USD": 0.0}


def build_rows(invoices):
    rows = []
    for inv in invoices:
        if inv["status"] == "cancelled":
            continue
        net = sum(float(l["qty"]) * float(l["unit_price"]) for l in inv["lines"])
        vat = round(net * VAT[inv["currency"]], 2)
        gross = net + vat
        rows.append([inv["id"], inv.get("customer"), inv["issued_at"][:10], inv["currency"],
                     f"{net:.2f}", f"{vat:.2f}", f"{gross:.2f}"])
    rows.sort(key=lambda r: r[0])
    return rows


def main(src, dst):
    with open(src) as fh:
        invoices = json.load(fh)
    with open(dst, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["invoice_id", "customer", "issued_date", "currency", "net", "vat", "gross"])
        w.writerows(build_rows(invoices))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
