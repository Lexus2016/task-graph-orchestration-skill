# Invoice export — spec (finance, v4, signed off)

`python3 export.py <invoices.json> <out.csv>` reads a JSON list of invoices and writes a CSV for the accounting import.

Input invoice: `{"id", "customer", "currency", "status", "issued_at", "lines": [{"sku", "qty", "unit_price"}]}`.
`unit_price` and `qty` may be numbers or numeric strings.

1. **Columns**, in this order: `invoice_id,customer,issued_date,currency,net,vat,gross`.
2. **Status:** skip `cancelled`. Include `paid` and `open`. Include `refunded` with **negative** net, vat and gross.
3. **Net** = sum of `qty * unit_price` over the lines, computed in exact decimal arithmetic (no binary floats), then rounded to 2 decimals **half-up**.
4. **VAT rate by currency:** EUR 21%, GBP 20%, USD 0%. `vat` = net × rate, rounded to 2 decimals **half-up**. `gross` = net + vat.
5. **issued_date** is the **UTC** calendar date of `issued_at` (it carries a UTC offset), formatted `YYYY-MM-DD`.
6. **Customer:** missing, null or blank → `UNKNOWN`. Keep names otherwise exactly as given (UTF-8, accents included).
7. **Duplicate invoice ids:** keep only the **last** occurrence in the input.
8. **Amounts:** always exactly 2 decimals, `.` as separator, no thousands separator, leading `-` for negatives.
9. **Order:** by issued_date ascending, then invoice_id ascending.
10. **Totals:** after the invoice rows, one row per currency (currencies sorted A–Z): `invoice_id` = `TOTAL`, `customer` and `issued_date` empty, `currency` set, and net/vat/gross = sums of that currency's rows above.
11. Output is UTF-8 CSV with a header row, written with standard CSV quoting (fields with commas or quotes are quoted).
