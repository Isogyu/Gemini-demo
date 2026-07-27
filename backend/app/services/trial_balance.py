"""試算表（Trial Balance）の集計。"""

from app.schemas.tax import AccountCategory, TrialBalance


def calculate_net_income_before_tax(trial_balance: TrialBalance) -> float:
    """収益 - 費用 で税引前当期純利益を求める。"""
    revenue = sum(
        line.credit - line.debit
        for line in trial_balance.lines
        if line.category == AccountCategory.REVENUE
    )
    expense = sum(
        line.debit - line.credit
        for line in trial_balance.lines
        if line.category == AccountCategory.EXPENSE
    )
    return revenue - expense


def is_balanced(trial_balance: TrialBalance) -> bool:
    debit = sum(line.debit for line in trial_balance.lines)
    credit = sum(line.credit for line in trial_balance.lines)
    return abs(debit - credit) < 1e-6
