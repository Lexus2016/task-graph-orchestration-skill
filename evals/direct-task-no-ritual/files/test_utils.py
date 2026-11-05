from utils import retry_count

def test_retry_count():
    assert retry_count(3) == 2
    assert retry_count(0) == 0
