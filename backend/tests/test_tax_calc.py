import pytest

from app.services.tax_calc import calculate_taxes


def test_total_tax_matches_effective_rate():
    result = calculate_taxes(100_000_000, effective_tax_rate=0.2974)
    assert result.total_tax == pytest.approx(29_740_000)


def test_components_sum_to_total():
    result = calculate_taxes(50_000_000)
    total = (
        result.corporate_tax
        + result.local_corporate_tax
        + result.enterprise_tax
        + result.inhabitant_tax
    )
    assert total == pytest.approx(result.total_tax)


def test_corporate_tax_is_largest_component():
    result = calculate_taxes(50_000_000)
    assert result.corporate_tax > result.enterprise_tax
    assert result.corporate_tax > result.inhabitant_tax
    assert result.corporate_tax > result.local_corporate_tax


def test_zero_or_negative_income_produces_no_tax():
    for income in (0, -10_000_000):
        result = calculate_taxes(income)
        assert result.total_tax == 0
        assert result.corporate_tax == 0


def test_invalid_rate_raises():
    with pytest.raises(ValueError):
        calculate_taxes(1_000_000, effective_tax_rate=1.5)
