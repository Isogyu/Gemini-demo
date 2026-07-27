import { MinusCircle, PlusCircle } from "lucide-react";

import { formatYen } from "@/lib/format";
import type { ReconciliationResult } from "@/lib/types";

interface Props {
  result: ReconciliationResult;
}

export function ReconciliationTable({ result }: Props) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-base font-semibold">別表四（加算・減算）イメージ</h2>
      <table className="mt-4 w-full text-sm" data-testid="reconciliation-table">
        <thead>
          <tr className="border-b border-slate-200 text-left text-slate-500">
            <th className="py-2">区分</th>
            <th className="py-2">項目</th>
            <th className="py-2 text-right">金額</th>
          </tr>
        </thead>
        <tbody>
          <tr className="border-b border-slate-100">
            <td className="py-2 text-slate-400">—</td>
            <td className="py-2 font-medium">当期純利益（税引前）</td>
            <td className="py-2 text-right tabular-nums font-medium">
              {formatYen(result.net_income_before_tax)}
            </td>
          </tr>
          {result.entries.map((entry, index) => (
            <tr key={`${entry.label}-${index}`} className="border-b border-slate-100">
              <td className="py-2">
                <span
                  className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs ${
                    entry.kind === "addition"
                      ? "bg-rose-50 text-rose-600"
                      : "bg-emerald-50 text-emerald-600"
                  }`}
                >
                  {entry.kind === "addition" ? (
                    <PlusCircle className="h-3 w-3" />
                  ) : (
                    <MinusCircle className="h-3 w-3" />
                  )}
                  {entry.kind === "addition" ? "加算" : "減算"}
                </span>
              </td>
              <td className="py-2">
                <div>{entry.label}</div>
                {entry.note && (
                  <div className="text-xs text-slate-400">{entry.note}</div>
                )}
              </td>
              <td className="py-2 text-right tabular-nums">
                {entry.kind === "addition" ? "+" : "−"}
                {formatYen(entry.amount)}
              </td>
            </tr>
          ))}
          <tr className="border-t-2 border-slate-300">
            <td className="py-2 text-slate-400">=</td>
            <td className="py-2 font-semibold">所得金額（課税所得）</td>
            <td
              className="py-2 text-right tabular-nums font-bold"
              data-testid="taxable-income-total"
            >
              {formatYen(result.taxable_income)}
            </td>
          </tr>
        </tbody>
      </table>

      <h3 className="mt-6 text-sm font-semibold text-slate-600">税額の内訳</h3>
      <dl className="mt-2 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
        {[
          ["法人税", result.tax.corporate_tax],
          ["地方法人税", result.tax.local_corporate_tax],
          ["法人住民税", result.tax.inhabitant_tax],
          ["法人事業税", result.tax.enterprise_tax],
        ].map(([label, value]) => (
          <div
            key={label as string}
            className="rounded-lg bg-slate-50 px-3 py-2"
          >
            <dt className="text-xs text-slate-500">{label as string}</dt>
            <dd className="font-medium tabular-nums">
              {formatYen(value as number)}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
