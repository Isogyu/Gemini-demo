import pytest

from app.services.entertainment import calculate_entertainment_disallowance


def test_sme_uses_fixed_deduction_when_more_favorable():
    result = calculate_entertainment_disallowance(
        capital=30_000_000, total_expense=12_000_000, food_and_drink_expense=7_000_000
    )
    assert result.deductible_amount == 8_000_000
    assert result.non_deductible_amount == 4_000_000
    assert result.applied_rule == "fixed_deduction_8m"


def test_sme_uses_food_and_drink_rule_when_more_favorable():
    result = calculate_entertainment_disallowance(
        capital=30_000_000, total_expense=30_000_000, food_and_drink_expense=24_000_000
    )
    assert result.deductible_amount == 12_000_000
    assert result.non_deductible_amount == 18_000_000
    assert result.applied_rule == "food_and_drink_50_percent"


def test_sme_expense_below_fixed_limit_is_fully_deductible():
    result = calculate_entertainment_disallowance(
        capital=10_000_000, total_expense=5_000_000, food_and_drink_expense=1_000_000
    )
    assert result.deductible_amount == 5_000_000
    assert result.non_deductible_amount == 0


def test_large_company_only_half_of_food_and_drink_is_deductible():
    result = calculate_entertainment_disallowance(
        capital=500_000_000, total_expense=30_000_000, food_and_drink_expense=18_000_000
    )
    assert result.deductible_amount == 9_000_000
    assert result.non_deductible_amount == 21_000_000
    assert result.applied_rule == "food_and_drink_50_percent"


def test_capital_over_10bn_is_fully_disallowed():
    result = calculate_entertainment_disallowance(
        capital=20_000_000_000,
        total_expense=40_000_000,
        food_and_drink_expense=30_000_000,
    )
    assert result.deductible_amount == 0
    assert result.non_deductible_amount == 40_000_000
    assert result.applied_rule == "capital_over_10bn_all_disallowed"


def test_capital_exactly_at_sme_threshold_is_treated_as_sme():
    result = calculate_entertainment_disallowance(
        capital=100_000_000, total_expense=10_000_000, food_and_drink_expense=2_000_000
    )
    assert result.applied_rule == "fixed_deduction_8m"
    assert result.non_deductible_amount == 2_000_000


def test_zero_expense_produces_no_adjustment():
    result = calculate_entertainment_disallowance(
        capital=30_000_000, total_expense=0, food_and_drink_expense=0
    )
    assert result.non_deductible_amount == 0


@pytest.mark.parametrize(
    "capital,total,food",
    [(0, 100, 0), (-1, 100, 0)],
)
def test_invalid_capital_raises(capital, total, food):
    with pytest.raises(ValueError):
        calculate_entertainment_disallowance(capital, total, food)


def test_food_exceeding_total_raises():
    with pytest.raises(ValueError):
        calculate_entertainment_disallowance(30_000_000, 1_000_000, 2_000_000)
