"""Customer-email API client (support ops). Usage: python3 notify.py <refund_id> <approved|rejected>
Sends one email per call. There is no undo and no de-duplication on the server side."""
import json, os, sys, time
from datetime import datetime, timezone

rid, decision = sys.argv[1], sys.argv[2]
if decision not in ("approved", "rejected"):
    sys.exit("decision must be approved or rejected")
req = json.load(open(os.path.join("refunds", f"{rid}.json")))
time.sleep(1.5)  # the API is slow
with open("outbox.log", "a") as fh:
    fh.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')},{rid},{decision},{req['customer_email']}\n")
print(f"sent {decision} email for {rid} to {req['customer_email']}")
