import pytest

def calc_roe(net_profit, equity):
    if equity <= 0: return None
    return (net_profit / equity) * 100

def calc_de(debt, equity):
    if debt == 0: return 0.0
    if equity <= 0: return None
    return debt / equity

@pytest.mark.parametrize("np, eq, expected", [
    (100, 1000, 10.0), (50, 1000, 5.0), (-50, 1000, -5.0),
    (100, 0, None), (100, -500, None), (0, 1000, 0.0),
    (200, 2000, 10.0), (300, 3000, 10.0), (400, 4000, 10.0), (500, 5000, 10.0)
])
def test_roe_calculation(np, eq, expected):
    # Tests positive, negative, and zero equity edge cases for ROE
    assert calc_roe(np, eq) == expected

@pytest.mark.parametrize("debt, eq, expected", [
    (0, 1000, 0.0), (0, -100, 0.0), (500, 1000, 0.5),
    (1000, 1000, 1.0), (2000, 1000, 2.0), (100, 0, None),
    (50, -50, None), (0, 0, 0.0), (10, 100, 0.1), (20, 100, 0.2)
])
def test_de_calculation(debt, eq, expected):
    # Tests debt-free companies and negative equity bounds for D/E
    assert calc_de(debt, eq) == expected
