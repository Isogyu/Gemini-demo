"""別表四（所得の金額の計算に関する明細書）イメージのシミュレーション。"""

from app.schemas.tax import (
    ReconciliationEntry,
    ReconciliationRequest,
    ReconciliationResult,
    TaxBreakdown,
)
from app.services.depreciation import calculate_depreciation_adjustment
from app.services.entertainment import calculate_entertainment_disallowance
from app.services.tax_calc import calculate_taxes
from app.services.trial_balance import calculate_net_income_before_tax


def _resolve_net_income(request: ReconciliationRequest) -> float:
    if request.net_income_before_tax is not None:
        return request.net_income_before_tax
    if request.trial_balance is not None:
        return calculate_net_income_before_tax(request.trial_balance)
    raise ValueError("net_income_before_tax または trial_balance が必要です")


def run_reconciliation(request: ReconciliationRequest) -> ReconciliationResult:
    net_income = _resolve_net_income(request)
    entries: list[ReconciliationEntry] = []

    entertainment = calculate_entertainment_disallowance(
        capital=request.capital,
        total_expense=request.entertainment.total_expense,
        food_and_drink_expense=request.entertainment.food_and_drink_expense,
    )
    if entertainment.non_deductible_amount > 0:
        entries.append(
            ReconciliationEntry(
                label="交際費等の損金不算入額",
                kind="addition",
                amount=entertainment.non_deductible_amount,
                note=f"適用ルール: {entertainment.applied_rule}",
            )
        )

    depreciation = calculate_depreciation_adjustment(request.depreciation_assets)
    for asset in depreciation.assets:
        if asset.excess > 0:
            entries.append(
                ReconciliationEntry(
                    label=f"減価償却の償却超過額（{asset.asset_name}）",
                    kind="addition",
                    amount=asset.excess,
                    note=f"会計上 {asset.booked_depreciation:,.0f} / 限度額 {asset.tax_limit:,.0f}",
                )
            )

    if request.other_additions > 0:
        entries.append(
            ReconciliationEntry(
                label="その他の加算",
                kind="addition",
                amount=request.other_additions,
            )
        )
    if request.other_subtractions > 0:
        entries.append(
            ReconciliationEntry(
                label="その他の減算",
                kind="subtraction",
                amount=request.other_subtractions,
            )
        )

    total_additions = sum(e.amount for e in entries if e.kind == "addition")
    total_subtractions = sum(e.amount for e in entries if e.kind == "subtraction")
    taxable_income = net_income + total_additions - total_subtractions

    tax = calculate_taxes(taxable_income, request.effective_tax_rate)

    return ReconciliationResult(
        company_name=request.company_name,
        fiscal_year=request.fiscal_year,
        capital=request.capital,
        net_income_before_tax=net_income,
        total_additions=total_additions,
        total_subtractions=total_subtractions,
        taxable_income=taxable_income,
        tax=TaxBreakdown(
            corporate_tax=tax.corporate_tax,
            local_corporate_tax=tax.local_corporate_tax,
            enterprise_tax=tax.enterprise_tax,
            inhabitant_tax=tax.inhabitant_tax,
            total_tax=tax.total_tax,
            effective_tax_rate=tax.effective_tax_rate,
        ),
        after_tax_profit=net_income - tax.total_tax,
        entries=entries,
    )
