import { formatYen } from "@/lib/format";
import type { ReconciliationResult } from "@/lib/types";

interface Props {
  result: ReconciliationResult;
}

export function IncomeChart({ result }: Props) {
  const bars = [
    {
      label: "税引前当期純利益",
      value: result.net_income_before_tax,
      color: "bg-sky-500",
    },
    { label: "課税所得", value: result.taxable_income, color: "bg-amber-500" },
    { label: "法人税等", value: result.tax.total_tax, color: "bg-rose-500" },
    {
      label: "税引後利益",
      value: result.after_tax_profit,
      color: "bg-emerald-500",
    },
  ];
  const max = Math.max(...bars.map((b) => Math.abs(b.value)), 1);

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-base font-semibold">利益・課税所得の比較</h2>
      <div className="mt-4 space-y-3">
        {bars.map((bar) => (
          <div key={bar.label}>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-600">{bar.label}</span>
              <span className="font-medium tabular-nums">
                {formatYen(bar.value)}
              </span>
            </div>
            <div className="mt-1 h-3 w-full rounded-full bg-slate-100">
              <div
                className={`h-3 rounded-full ${bar.color}`}
                style={{
                  width: `${Math.max(
                    (Math.abs(bar.value) / max) * 100,
                    bar.value === 0 ? 0 : 2
                  )}%`,
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
