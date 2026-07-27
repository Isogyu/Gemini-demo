"""法人税等の概算計算。

法定の各税目（法人税・地方法人税・法人住民税・事業税）の比率で按分しつつ、
合計額が指定された実効税率と一致するようにスケーリングする簡易モデル。
"""

from dataclasses import dataclass

DEFAULT_EFFECTIVE_TAX_RATE = 0.2974

CORPORATE_TAX_RATE = 0.232
LOCAL_CORPORATE_TAX_RATE = 0.103  # 法人税額に対して
INHABITANT_TAX_RATE = 0.07  # 法人税額に対して（法人税割）
ENTERPRISE_TAX_RATE = 0.07  # 所得に対して（特別法人事業税を含む）


@dataclass(frozen=True)
class TaxAmounts:
    corporate_tax: float
    local_corporate_tax: float
    enterprise_tax: float
    inhabitant_tax: float
    total_tax: float
    effective_tax_rate: float


def calculate_taxes(
    taxable_income: float, effective_tax_rate: float = DEFAULT_EFFECTIVE_TAX_RATE
) -> TaxAmounts:
    if not 0 < effective_tax_rate < 1:
        raise ValueError("effective_tax_rate must be between 0 and 1")

    if taxable_income <= 0:
        return TaxAmounts(0.0, 0.0, 0.0, 0.0, 0.0, effective_tax_rate)

    corporate = taxable_income * CORPORATE_TAX_RATE
    local_corporate = corporate * LOCAL_CORPORATE_TAX_RATE
    inhabitant = corporate * INHABITANT_TAX_RATE
    enterprise = taxable_income * ENTERPRISE_TAX_RATE
    statutory_total = corporate + local_corporate + inhabitant + enterprise

    target_total = taxable_income * effective_tax_rate
    scale = target_total / statutory_total

    return TaxAmounts(
        corporate_tax=corporate * scale,
        local_corporate_tax=local_corporate * scale,
        enterprise_tax=enterprise * scale,
        inhabitant_tax=inhabitant * scale,
        total_tax=target_total,
        effective_tax_rate=effective_tax_rate,
    )
