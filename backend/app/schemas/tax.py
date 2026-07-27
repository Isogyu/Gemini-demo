from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class AccountCategory(str, Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class TrialBalanceLine(BaseModel):
    account_code: str
    account_name: str
    category: AccountCategory
    debit: float = 0.0
    credit: float = 0.0


class TrialBalance(BaseModel):
    name: str
    fiscal_year: int
    lines: List[TrialBalanceLine]


class EntertainmentInput(BaseModel):
    """交際費等の損金不算入計算のインプット。"""

    total_expense: float = Field(0.0, ge=0, description="交際費等の総額")
    food_and_drink_expense: float = Field(
        0.0, ge=0, description="うち接待飲食費（1人1万円以下の少額飲食費を除く）"
    )


class DepreciationAssetInput(BaseModel):
    asset_name: str
    booked_depreciation: float = Field(0.0, ge=0, description="会計上の減価償却費")
    tax_limit: float = Field(0.0, ge=0, description="税務上の償却限度額")


class ReconciliationRequest(BaseModel):
    """別表四シミュレーションのリクエスト。"""

    company_name: str = "Sample Corporation"
    fiscal_year: int = 2025
    capital: float = Field(..., gt=0, description="資本金の額（円）")
    net_income_before_tax: Optional[float] = Field(
        None, description="税引前当期純利益。未指定の場合は試算表から算出"
    )
    trial_balance: Optional[TrialBalance] = None
    entertainment: EntertainmentInput = EntertainmentInput()
    depreciation_assets: List[DepreciationAssetInput] = []
    other_additions: float = Field(0.0, ge=0, description="その他の加算額")
    other_subtractions: float = Field(0.0, ge=0, description="その他の減算額")
    effective_tax_rate: float = Field(0.2974, gt=0, lt=1, description="実効税率")


class ReconciliationEntry(BaseModel):
    """別表四の加算・減算1行。"""

    label: str
    kind: str  # "addition" | "subtraction"
    amount: float
    note: str = ""


class TaxBreakdown(BaseModel):
    corporate_tax: float
    local_corporate_tax: float
    enterprise_tax: float
    inhabitant_tax: float
    total_tax: float
    effective_tax_rate: float


class ReconciliationResult(BaseModel):
    company_name: str
    fiscal_year: int
    capital: float
    net_income_before_tax: float
    total_additions: float
    total_subtractions: float
    taxable_income: float
    tax: TaxBreakdown
    after_tax_profit: float
    entries: List[ReconciliationEntry]
