"""Validate v2 configs: python3 validate.py configs/*.json"""
import json
import sys

bad = 0
for path in sys.argv[1:]:
    d = json.load(open(path))
    s = d.get("server") or {}
    ok = d.get("version") == 2 and isinstance(d.get("name"), str) \
        and isinstance(s.get("port"), int) and 1 <= s["port"] <= 65535 and isinstance(s.get("host"), str)
    print(("OK   " if ok else "FAIL ") + path)
    bad += not ok
sys.exit(1 if bad else 0)
