# Order normalisation rules (import contract v2)

For every `orders/<id>.json` there must be exactly one `normalized/<id>.json`:

```json
{"order_id": "...", "email": "...", "country": "XX", "total_cents": 0,
 "items": [{"sku": "...", "qty": 0, "unit_cents": 0}], "created_utc": "YYYY-MM-DDTHH:MM:SSZ", "source_sha256": "..."}
```

1. `email`: trimmed and lower-cased.
2. `country`: ISO 3166-1 alpha-2 from the table below (match the raw name case-insensitively, trimmed).
   Netherlands→NL, Germany→DE, United Kingdom→GB, Great Britain→GB, France→FR, Belgium→BE, Spain→ES, Poland→PL.
3. `items`: sorted by `sku`; `unit_cents` = price × 100 as an exact integer (prices have at most 2 decimals).
4. `total_cents` = Σ qty × unit_cents.
5. `created_utc`: the order's `created_at` converted to UTC, second precision, `Z` suffix.
6. `source_sha256`: hex SHA-256 of the raw bytes of `orders/<id>.json` the output was built from.
   An output whose hash does not match the current input is **stale** and must be rebuilt.
7. No other files in `normalized/`.
