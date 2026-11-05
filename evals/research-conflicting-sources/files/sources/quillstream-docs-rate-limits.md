# Quillstream API — Rate limits
_Official documentation · last updated 2026-03-02_

Every API key is limited per minute, counted across all endpoints.

| Plan | Requests per minute |
|---|---|
| Free | 600 |
| Paid | 600 |

Exceeding the limit returns HTTP 429 with a `Retry-After` header.
