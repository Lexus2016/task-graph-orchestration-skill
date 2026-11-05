def apply_discount(amount_cents: int, percent: int) -> int:
    """Return amount after a percentage discount, rounding the discount down."""
    return amount_cents - amount_cents * percent // 100
