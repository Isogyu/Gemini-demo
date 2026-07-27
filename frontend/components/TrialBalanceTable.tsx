import { formatYen } from "@/lib/format";
import type { TrialBalance } from "@/lib/types";

interface Props {
  trialBalance: TrialBalance;
}

const CATEGORY_LABELS: Record<string, string> = {
  asset: "資産",
  liability: "負債",
  equity: "純資産",
  revenue: "収益",
  expense: "費用",
};

export function TrialBalanceTable({ trialBalance }: Props) {
  const totalDebit = trialBalance.lines.reduce((sum, l) => sum + l.debit, 0);
  const totalCredit = trialBalance.lines.reduce((sum, l) => sum + l.credit, 0);

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-base font-semibold">{trialBalance.name}</h2>
      <table className="mt-4 w-full text-sm" data-testid="trial-balance-table">
        <thead>
          <tr className="border-b border-slate-200 text-left text-slate-500">
            <th className="py-2">コード</th>
            <th className="py-2">勘定科目</th>
            <th className="py-2">区分</th>
            <th className="py-2 text-right">借方</th>
            <th className="py-2 text-right">貸方</th>
          </tr>
        </thead>
        <tbody>
          {trialBalance.lines.map((line) => (
            <tr key={line.account_code} className="border-b border-slate-100">
              <td className="py-1.5 text-slate-400">{line.account_code}</td>
              <td className="py-1.5">{line.account_name}</td>
              <td className="py-1.5 text-slate-500">
                {CATEGORY_LABELS[line.category] ?? line.category}
              </td>
              <td className="py-1.5 text-right tabular-nums">
                {line.debit ? formatYen(line.debit) : "—"}
              </td>
              <td className="py-1.5 text-right tabular-nums">
                {line.credit ? formatYen(line.credit) : "—"}
              </td>
            </tr>
          ))}
          <tr className="border-t-2 border-slate-300 font-semibold">
            <td className="py-2" colSpan={3}>
              合計
            </td>
            <td className="py-2 text-right tabular-nums">
              {formatYen(totalDebit)}
            </td>
            <td className="py-2 text-right tabular-nums">
              {formatYen(totalCredit)}
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  );
}
