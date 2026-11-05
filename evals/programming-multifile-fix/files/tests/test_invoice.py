from pricing.invoice import invoice_line


def test_invoice_line_two_decimals():
    assert invoice_line("Widget", 1250) == "Widget: $12.50"
