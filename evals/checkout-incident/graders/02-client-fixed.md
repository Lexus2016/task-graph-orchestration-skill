---
type: llm
focus: trace
weight: 1
---

Hidden client tests pass: no retry on non-retryable 4xx (e.g. 400), retries on timeout/5xx/429 with increasing sleeps, attempts stay capped at the configured value (5) by default (checked by code).
