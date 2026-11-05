"""Minimal PSP client used by the payments service."""
import time


class PSPError(Exception):
    def __init__(self, status, message=""):
        super().__init__(f"{status} {message}")
        self.status = status


class Timeout(Exception):
    pass


def call_with_retry(send, max_attempts=5, sleep=time.sleep):
    """Call send() until it succeeds or attempts run out.

    send() returns the PSP response or raises Timeout / PSPError.
    """
    last = None
    for attempt in range(1, max_attempts + 1):
        try:
            return send()
        except (Timeout, PSPError) as e:  # retry everything, immediately
            last = e
    raise last
