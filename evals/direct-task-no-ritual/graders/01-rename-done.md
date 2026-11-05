---
type: llm
focus: trace
weight: 1
---

utils.py defines retries_left and test_utils.py imports and calls retries_left; no reference to retry_count remains.
