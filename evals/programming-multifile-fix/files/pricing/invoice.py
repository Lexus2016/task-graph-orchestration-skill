def invoice_line(name: str, cents: int) -> str:
    return f"{name}: ${cents / 100}"
