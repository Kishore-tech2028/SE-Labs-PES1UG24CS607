import pytest
from income_tax import taxable_income, tax_due, refund_status


# ---------- taxable_income ----------
def test_new_regime():
    assert taxable_income(1000000, "new", 0) == 925000

def test_old_regime_investment_capped():
    # investments 200000 -> capped to 150000, deduction = 200000
    assert taxable_income(1000000, "old", 200000) == 800000

def test_negative_gross():
    with pytest.raises(ValueError):
        taxable_income(-1, "new", 0)

def test_unknown_regime():
    with pytest.raises(ValueError):
        taxable_income(500000, "other", 0)

def test_taxable_negative_returns_zero():
    assert taxable_income(50000, "new", 0) == 0


# ---------- tax_due ----------
def test_below_exemption():
    assert tax_due(200000, 30) == 0

def test_negative_taxable():
    with pytest.raises(ValueError):
        tax_due(-1, 30)

def test_super_senior():
    assert tax_due(600000, 85) == 5000       # slab 100000 * 5%

def test_senior():
    assert tax_due(400000, 65) == 5000       # slab 100000 * 5%

def test_high_slab():
    assert tax_due(1000000, 30) == 112500    # 12500 + 500000*20%


# ---------- refund_status ----------
def test_refund_on_time():
    assert refund_status(1000, 500, True) == "refund"

def test_refund_delayed():
    assert refund_status(1000, 500, False) == "refund delayed"

def test_pay_balance():
    assert refund_status(500, 1000, True) == "pay balance"

def test_pay_balance_penalty():
    assert refund_status(500, 1000, False) == "pay balance with penalty"

def test_settled():
    assert refund_status(500, 500, True) == "settled"

# ---- add to the previous tests ----

# taxable_income: untested branches / boundaries
def test_old_regime_investment_below_cap():
    assert taxable_income(1000000, "old", 100000) == 850000   # cap NOT applied

def test_old_regime_investment_exactly_cap():
    assert taxable_income(1000000, "old", 150000) == 800000   # 150000 > 150000 is False

def test_zero_gross():
    assert taxable_income(0, "new", 0) == 0

def test_taxable_exactly_zero():
    assert taxable_income(75000, "new", 0) == 0               # taxable < 0 False

# tax_due: age boundaries and slab boundaries
@pytest.mark.parametrize("taxable, age, expected", [
    (0, 30, 0),
    (250000, 59, 0),         # exempt limit, age < 60
    (300000, 60, 0),         # age >= 60 boundary
    (350000, 60, 2500),
    (500000, 80, 0),         # age >= 80 boundary
    (550000, 80, 2500),
    (500000, 30, 12500),     # slab exactly 250000 (<= True)
    (600000, 30, 32500),     # slab > 250000 (<= False)
])
def test_tax_due_boundaries(taxable, age, expected):
    assert tax_due(taxable, age) == expected

# refund_status: already all covered, but add boundary
def test_settled_late():
    assert refund_status(500, 500, False) == "settled"