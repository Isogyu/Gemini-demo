"use client";

import { AlertCircle, Loader2, Play, Sparkles, Table2 } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { IncomeChart } from "@/components/IncomeChart";
import { ReconciliationTable } from "@/components/ReconciliationTable";
import { SummaryCards } from "@/components/SummaryCards";
import { TrialBalanceTable } from "@/components/TrialBalanceTable";
import { fetchSamples, postReconciliation } from "@/lib/api";
import type { ReconciliationResult, SampleDataset } from "@/lib/types";

export default function Home() {
  const [samples, setSamples] = useState<SampleDataset[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [effectiveRate, setEffectiveRate] = useState<number>(29.74);
  const [result, setResult] = useState<ReconciliationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showTrialBalance, setShowTrialBalance] = useState(false);

  useEffect(() => {
    fetchSamples()
      .then((data) => {
        setSamples(data);
        setSelectedId(data[0]?.id ?? "");
      })
      .catch(() => setError("サンプルデータの取得に失敗しました。API を確認してください。"));
  }, []);

  const selected = samples.find((s) => s.id === selectedId);

  const runSimulation = useCallback(async () => {
    if (!selected) return;
    setLoading(true);
    setError(null);
    try {
      const data = await postReconciliation({
        company_name: selected.company_name,
        fiscal_year: selected.fiscal_year,
        capital: selected.capital,
        trial_balance: selected.trial_balance,
        entertainment: selected.entertainment,
        depreciation_assets: selected.depreciation_assets,
        other_additions: selected.other_additions,
        other_subtractions: selected.other_subtractions,
        effective_tax_rate: effectiveRate / 100,
      });
      setResult(data);
    } catch {
      setError("シミュレーションの実行に失敗しました。");
    } finally {
      setLoading(false);
    }
  }, [selected, effectiveRate]);

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            法人税・財務諸表 税務調整シミュレーター
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            試算表を読み込み、交際費・減価償却の税務調整を反映した課税所得と法人税等を試算します。
          </p>
        </div>
        <Link
          href="/debate"
          className="inline-flex items-center gap-1 rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
        >
          <Sparkles className="h-3 w-3" />
          ディベート立論アナライザー
        </Link>
      </header>

      <section className="mt-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <label className="flex-1 text-sm">
            <span className="text-slate-600">サンプル試算表</span>
            <select
              data-testid="sample-select"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
            >
              {samples.map((sample) => (
                <option key={sample.id} value={sample.id}>
                  {sample.label}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm sm:w-48">
            <span className="text-slate-600">実効税率（%）</span>
            <input
              data-testid="effective-rate-input"
              type="number"
              step="0.01"
              min="0.01"
              max="99"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
              value={effectiveRate}
              onChange={(e) => setEffectiveRate(Number(e.target.value))}
            />
          </label>
          <button
            data-testid="run-simulation"
            onClick={runSimulation}
            disabled={loading || !selected}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            シミュレーション実行
          </button>
        </div>

        {selected && (
          <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-slate-500">
            <span>会社名: {selected.company_name}</span>
            <span>事業年度: {selected.fiscal_year}</span>
            <span>資本金: {selected.capital.toLocaleString("ja-JP")} 円</span>
            <button
              onClick={() => setShowTrialBalance((v) => !v)}
              className="inline-flex items-center gap-1 text-slate-700 underline"
            >
              <Table2 className="h-3 w-3" />
              試算表を{showTrialBalance ? "隠す" : "表示"}
            </button>
          </div>
        )}
      </section>

      {error && (
        <div
          data-testid="error-banner"
          className="mt-4 flex items-center gap-2 rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-700"
        >
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}

      {showTrialBalance && selected && (
        <div className="mt-6">
          <TrialBalanceTable trialBalance={selected.trial_balance} />
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-6">
          <SummaryCards result={result} />
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <IncomeChart result={result} />
            <ReconciliationTable result={result} />
          </div>
        </div>
      )}
    </main>
  );
}
