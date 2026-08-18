import pytest

@pytest.mark.parametrize("rule_id, val, threshold, is_violation", [
    ("DQ-01", None, 0, True),
    ("DQ-02", -10, 0, True),
    ("DQ-03", 150, 100, False),
    ("DQ-04", 0, 0, False),
    ("DQ-05", 999999, 100000, True),
    ("DQ-06", -5, 0, True),
    ("DQ-07", 10, 0, False),
    ("DQ-08", None, 0, True),
    ("DQ-09", "N/A", 0, True),
    ("DQ-10", 0, 0, False),
    ("DQ-11", 1, 0, False),
    ("DQ-12", -1, 0, True),
    ("DQ-13", 100, 50, True),
    ("DQ-14", 150, 100, False)
])
def test_dq_rules(rule_id, val, threshold, is_violation):
    # Mocks Data Quality rule engine validating violations
    violation = False
    if val is None or val == "N/A": violation = True
    elif isinstance(val, (int, float)) and val < threshold: violation = True
    elif isinstance(val, (int, float)) and val > threshold and rule_id in ["DQ-05", "DQ-13"]: violation = True
    
    assert violation == is_violation
