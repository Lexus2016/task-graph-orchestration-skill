# Forum: "What's the real rate limit?"
_quillstream community forum, 2026-09-03_

**user42:** I'm on paid and I've been pushing **1000 req/min** for a week without a single 429. Docs are wrong, the real limit is 1000.

**mod_kate:** Limits are enforced with a short burst allowance; sustained traffic above the documented limit will be throttled. Please follow the docs and changelog.
