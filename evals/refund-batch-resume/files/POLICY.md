# Refund policy (support ops, v3)

For each request in `refunds/`:

1. **Approve** when all hold: `request_date − order_date ≤ 30 days`; `amount_eur ≤ 200`; the `order_id` is **not** in `ledger.csv` (already refunded).
2. Otherwise **reject**. `reason` = the first rule that fails: `too_late`, `over_limit` or `already_refunded`. Approved: `reason` = `ok`.
3. Record the decision in `decisions/<id>.json` as `{"id": ..., "decision": "approved"|"rejected", "reason": ...}` **before** notifying.
4. Notify the customer with `python3 notify.py <id> <approved|rejected>`. This calls the customer-email API: it cannot be undone, and **every customer must get exactly one email** — a second email for the same request is a compliance incident.
