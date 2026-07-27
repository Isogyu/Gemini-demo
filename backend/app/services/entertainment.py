"""交際費等の損金不算入額の計算。

資本金の額に応じて次のルールで判定する（MVP 用に簡略化した現行制度ベース）。

* 資本金 1 億円以下（中小法人）
    - 年 800 万円の定額控除限度額 と 接待飲食費の 50% の
      いずれか有利な方を損金算入できる。
* 資本金 1 億円超 100 億円以下
    - 接待飲食費の 50% のみ損金算入できる。
* 資本金 100 億円超
    - 全額損金不算入。
"""

from dataclasses import dataclass

SMALL_COMPANY_CAPITAL_THRESHOLD = 100_000_000
LARGE_COMPANY_CAPITAL_THRESHOLD = 10_000_000_000
FIXED_DEDUCTION_LIMIT = 8_000_000
FOOD_AND_DRINK_DEDUCTIBLE_RATIO = 0.5


@dataclass(frozen=True)
class EntertainmentResult:
    total_expense: float
    deductible_amount: float
    non_deductible_amount: float
    applied_rule: str


def calculate_entertainment_disallowance(
    capital: float,
    total_expense: float,
    food_and_drink_expense: float,
) -> EntertainmentResult:
    if capital <= 0:
        raise ValueError("capital must be positive")
    if total_expense < 0 or food_and_drink_expense < 0:
        raise ValueError("expenses must not be negative")
    if food_and_drink_expense > total_expense:
        raise ValueError("food_and_drink_expense must not exceed total_expense")

    food_and_drink_limit = food_and_drink_expense * FOOD_AND_DRINK_DEDUCTIBLE_RATIO

    if capital > LARGE_COMPANY_CAPITAL_THRESHOLD:
        deductible = 0.0
        rule = "capital_over_10bn_all_disallowed"
    elif capital > SMALL_COMPANY_CAPITAL_THRESHOLD:
        deductible = food_and_drink_limit
        rule = "food_and_drink_50_percent"
    else:
        fixed_limit = min(FIXED_DEDUCTION_LIMIT, total_expense)
        if food_and_drink_limit >= fixed_limit:
            deductible = food_and_drink_limit
            rule = "food_and_drink_50_percent"
        else:
            deductible = fixed_limit
            rule = "fixed_deduction_8m"

    deductible = min(deductible, total_expense)
    return EntertainmentResult(
        total_expense=total_expense,
        deductible_amount=deductible,
        non_deductible_amount=total_expense - deductible,
        applied_rule=rule,
    )
