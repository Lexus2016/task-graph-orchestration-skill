from pricing.cart import total


def test_coupon_only():
    assert total([(1000, 5)], coupon_percent=15) == 4250


def test_bulk_only():
    assert total([(1000, 10)]) == 9000
