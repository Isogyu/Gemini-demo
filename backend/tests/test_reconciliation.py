import pytest

from app.schemas.tax import (
    DepreciationAssetInput,
    EntertainmentInput,
    ReconciliationRequest,
)
from app.services.reconciliation import run_reconciliation
from app.services.samples import get_sample, load_samples
from app.services.trial_balance import calculate_net_income_before_tax, is_balanced


def build_request(**overrides) -> ReconciliationRequest:
    defaults = dict(
        capital=30_000_000,
        net_income_before_tax=20_000_000,
        entertainment=EntertainmentInput(
            total_expense=12_000_000, food_and_drink_expense=7_000_000
        ),
        depreciation_assets=[
            DepreciationAssetInput(
                asset_name="本社建物",
                booked_depreciation=5_000_000,
                tax_limit=4_200_000,
            )
        ],
    )
    defaults.update(overrides)
    return ReconciliationRequest(**defaults)


def test_taxable_income_includes_all_additions():
    result = run_reconciliation(build_request())
    assert result.total_additions == 4_800_000
    assert result.total_subtractions == 0
    assert result.taxable_income == 24_800_000


def test_after_tax_profit_uses_book_income_minus_tax():
    result = run_reconciliation(build_request())
    assert result.tax.total_tax == pytest.approx(24_800_000 * 0.2974)
    assert result.after_tax_profit == pytest.approx(20_000_000 - result.tax.total_tax)


def test_entries_contain_labelled_addition_rows():
    result = run_reconciliation(build_request())
    labels = [e.label for e in result.entries]
    assert "交際費等の損金不算入額" in labels
    assert any("償却超過額" in label for label in labels)
    assert all(e.kind in {"addition", "subtraction"} for e in result.entries)


def test_subtractions_reduce_taxable_income():
    result = run_reconciliation(build_request(other_subtractions=3_000_000))
    assert result.total_subtractions == 3_000_000
    assert result.taxable_income == 21_800_000


def test_net_income_is_derived_from_trial_balance_when_omitted():
    sample = get_sample("sme-2025")
    request = sample.to_request()
    assert request.net_income_before_tax is None
    result = run_reconciliation(request)
    assert result.net_income_before_tax == 20_000_000
    assert result.taxable_income == 24_800_000


def test_missing_income_source_raises():
    with pytest.raises(ValueError):
        run_reconciliation(
            ReconciliationRequest(capital=10_000_000, net_income_before_tax=None)
        )


def test_loss_making_company_pays_no_tax():
    result = run_reconciliation(
        build_request(
            net_income_before_tax=-50_000_000,
            entertainment=EntertainmentInput(),
            depreciation_assets=[],
        )
    )
    assert result.taxable_income == -50_000_000
    assert result.tax.total_tax == 0
    assert result.after_tax_profit == -50_000_000


@pytest.mark.parametrize("sample", load_samples(), ids=lambda s: s.id)
def test_sample_trial_balances_are_balanced(sample):
    assert is_balanced(sample.trial_balance)
    assert calculate_net_income_before_tax(sample.trial_balance) > 0


def test_large_company_sample_adjustments():
    result = run_reconciliation(get_sample("large-2025").to_request())
    assert result.net_income_before_tax == 210_000_000
    # 交際費 21,000,000 + 償却超過 7,000,000 + その他加算 2,000,000
    assert result.total_additions == 30_000_000
    assert result.total_subtractions == 1_000_000
    assert result.taxable_income == 239_000_000
