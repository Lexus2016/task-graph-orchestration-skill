"""Migrate one service config from v1 to v2 in place: python3 migrate.py configs/<file>.json"""
import json
import sys

path = sys.argv[1]
data = json.load(open(path))
migrated = {
    "version": 2,
    "name": data.get("name"),
    "server": {"port": data.get("port"), "host": data.get("host", "0.0.0.0")},
}
json.dump(migrated, open(path, "w"), indent=2)
print(f"migrated {path}")
