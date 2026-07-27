"""減価償却超過額（償却限度超過額）の計算。"""

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class AssetDepreciationResult:
    asset_name: str
    booked_depreciation: float
    tax_limit: float
    excess: float
    shortfall: float


@dataclass(frozen=True)
class DepreciationResult:
    assets: List[AssetDepreciationResult]
    total_excess: float
    total_shortfall: float


def calculate_asset_depreciation_excess(
    asset_name: str, booked_depreciation: float, tax_limit: float
) -> AssetDepreciationResult:
    if booked_depreciation < 0 or tax_limit < 0:
        raise ValueError("depreciation values must not be negative")
    diff = booked_depreciation - tax_limit
    return AssetDepreciationResult(
        asset_name=asset_name,
        booked_depreciation=booked_depreciation,
        tax_limit=tax_limit,
        excess=max(diff, 0.0),
        shortfall=max(-diff, 0.0),
    )


def calculate_depreciation_adjustment(assets: Iterable) -> DepreciationResult:
    """各資産の償却超過額を集計する。

    超過額は加算（損金不算入）、償却不足額は繰越超過額がある場合のみ
    減算対象となるが、MVP では情報として保持するにとどめる。
    """
    results = [
        calculate_asset_depreciation_excess(
            a.asset_name, a.booked_depreciation, a.tax_limit
        )
        for a in assets
    ]
    return DepreciationResult(
        assets=results,
        total_excess=sum(r.excess for r in results),
        total_shortfall=sum(r.shortfall for r in results),
    )
