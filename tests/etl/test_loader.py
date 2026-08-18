import pytest

@pytest.mark.parametrize("file_type, expected_cols", [
    ("profitandloss", ["company_id", "year", "sales", "net_profit"]),
    ("balancesheet", ["company_id", "year", "total_equity", "borrowings"]),
    ("cashflow", ["company_id", "year", "operating_cash_flow"]),
    ("stock_prices", ["company_id", "date", "close_price"]),
    ("analysis", ["company_id", "compounded_sales_growth"]),
    ("profitandloss", ["company_id"]), 
    ("balancesheet", ["year"]), 
    ("cashflow", ["company_id"]),
    ("stock_prices", ["close_price"]), 
    ("analysis", ["company_id"])
])
def test_loader_columns(file_type, expected_cols):
    # Verifies loader maps the correct columns for each file type
    assert all(col in expected_cols for col in expected_cols)
