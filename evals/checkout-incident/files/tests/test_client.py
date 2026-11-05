import pytest

from services.payments.client import PSPError, Timeout, call_with_retry


def test_returns_first_success():
    assert call_with_retry(lambda: "ok", sleep=lambda s: None) == "ok"


def test_gives_up_after_max_attempts():
    calls = []

    def send():
        calls.append(1)
        raise Timeout()

    with pytest.raises(Timeout):
        call_with_retry(send, max_attempts=3, sleep=lambda s: None)
    assert len(calls) == 3
