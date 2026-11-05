import csv
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def run(invoices, tmp_path):
    src, dst = tmp_path / "in.json", tmp_path / "out.csv"
    src.write_text(json.dumps(invoices), encoding="utf-8")
    subprocess.run([sys.executable, os.path.join(ROOT, "export.py"), str(src), str(dst)], check=True)
    with open(dst, encoding="utf-8") as fh:
        return list(csv.reader(fh))


def inv(i, **kw):
    base = {"id": i, "customer": "Acme", "currency": "EUR", "status": "paid",
            "issued_at": "2026-10-02T10:00:00+00:00", "lines": [{"sku": "A", "qty": 2, "unit_price": 50}]}
    base.update(kw)
    return base


def test_header(tmp_path):
    assert run([inv("INV-1")], tmp_path)[0] == ["invoice_id", "customer", "issued_date", "currency", "net", "vat", "gross"]


def test_amounts_eur(tmp_path):
    row = run([inv("INV-1")], tmp_path)[1]
    assert row[4:] == ["100.00", "21.00", "121.00"]


def test_cancelled_skipped(tmp_path):
    ids = [r[0] for r in run([inv("INV-1"), inv("INV-2", status="cancelled")], tmp_path)[1:]]
    assert "INV-2" not in ids
