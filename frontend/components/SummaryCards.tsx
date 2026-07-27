import { Calculator, Landmark, TrendingUp, Wallet } from "lucide-react";

import { formatPercent, formatYen } from "@/lib/format";
import type { ReconciliationResult } from "@/lib/types";

interface Props {
  result: ReconciliationResult;
}

export function SummaryCards({ result }: Props) {
  const cards = [
    {
      label: "税引前当期純利益（会計）",
      value: formatYen(result.net_income_before_tax),
      icon: TrendingUp,
      accent: "text-sky-600",
      note: "試算表ベース",
      testId: "card-net-income",
    },
    {
      label: "課税所得（別表四 後）",
      value: formatYen(result.taxable_income),
      icon: Calculator,
      accent: "text-amber-600",
      note: `加算 ${formatYen(result.total_additions)} / 減算 ${formatYen(
        result.total_subtractions
      )}`,
      testId: "card-taxable-income",
    },
    {
      label: "法人税等 合計",
      value: formatYen(result.tax.total_tax),
      icon: Landmark,
      accent: "text-rose-600",
      note: `実効税率 ${formatPercent(result.tax.effective_tax_rate)}`,
      testId: "card-total-tax",
    },
    {
      label: "税引後利益",
      value: formatYen(result.after_tax_profit),
      icon: Wallet,
      accent: "text-emerald-600",
      note: "税引前利益 − 法人税等",
      testId: "card-after-tax",
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => (
        <div
          key={card.label}
          data-testid={card.testId}
          className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-500">{card.label}</p>
            <card.icon className={`h-5 w-5 ${card.accent}`} />
          </div>
          <p className="mt-3 text-2xl font-bold tracking-tight">{card.value}</p>
          <p className="mt-1 text-xs text-slate-400">{card.note}</p>
        </div>
      ))}
    </div>
  );
}
