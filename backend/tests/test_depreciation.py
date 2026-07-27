import pytest

from app.schemas.tax import DepreciationAssetInput
from app.services.depreciation import (
    calculate_asset_depreciation_excess,
    calculate_depreciation_adjustment,
)


def test_excess_when_booked_exceeds_limit():
    result = calculate_asset_depreciation_excess("本社建物", 5_000_000, 4_200_000)
    assert result.excess == 800_000
    assert result.shortfall == 0


def test_shortfall_when_booked_below_limit():
    result = calculate_asset_depreciation_excess("社用車", 2_000_000, 3_000_000)
    assert result.excess == 0
    assert result.shortfall == 1_000_000


def test_no_adjustment_when_equal():
    result = calculate_asset_depreciation_excess("備品", 1_000_000, 1_000_000)
    assert result.excess == 0
    assert result.shortfall == 0


def test_negative_values_raise():
    with pytest.raises(ValueError):
        calculate_asset_depreciation_excess("備品", -1, 1_000_000)


def test_totals_are_aggregated_across_assets():
    assets = [
        DepreciationAssetInput(
            asset_name="A", booked_depreciation=5_000_000, tax_limit=4_200_000
        ),
        DepreciationAssetInput(
            asset_name="B", booked_depreciation=3_000_000, tax_limit=3_500_000
        ),
        DepreciationAssetInput(
            asset_name="C", booked_depreciation=1_200_000, tax_limit=1_000_000
        ),
    ]
    result = calculate_depreciation_adjustment(assets)
    assert result.total_excess == 1_000_000
    assert result.total_shortfall == 500_000
    assert len(result.assets) == 3


def test_empty_asset_list():
    result = calculate_depreciation_adjustment([])
    assert result.total_excess == 0
    assert result.total_shortfall == 0
