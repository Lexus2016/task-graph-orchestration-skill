from .discount import apply_discount

BULK_THRESHOLD = 10
BULK_PERCENT = 10


def total(items, coupon_percent=0):
    """items: list of (unit_price_cents, quantity). Returns the amount to charge in cents."""
    subtotal = sum(price * qty for price, qty in items)
    quantity = sum(qty for _, qty in items)
    bulk_percent = BULK_PERCENT if quantity >= BULK_THRESHOLD else 0
    after_coupon = apply_discount(subtotal, coupon_percent)
    return apply_discount(after_coupon, bulk_percent)
