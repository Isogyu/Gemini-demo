"use client";

import { AlertCircle, Calculator, Loader2, Play, Sparkles } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ArgumentTree } from "@/components/debate/ArgumentTree";
import { DocumentInputCard } from "@/components/debate/DocumentInputCard";
import { EvidencePanel } from "@/components/debate/EvidencePanel";
import { IssueMap } from "@/components/debate/IssueMap";
import { RebuttalList } from "@/components/debate/RebuttalList";
import { analyzeDebate, fetchDebateSamples } from "@/lib/debateApi";
import type { DebateAnalysis, DebateSample } from "@/lib/debateTypes";

type TabId = "issues" | "rebuttals" | "structure" | "evidence";

const TABS: { id: TabId; label: string }[] = [
  { id: "issues", label: "論点マップ" },
  { id: "rebuttals", label: "反駁・想定尋問" },
  { id: "structure", label: "立論の構造" },
  { id: "evidence", label: "出典チェック" },
];

const EMPTY = { title: "", text: "" };

export default function DebatePage() {
  const [topic, setTopic] = useState("");
  const [pro, setPro] = useState(EMPTY);
  const [con, setCon] = useState(EMPTY);
  const [samples, setSamples] = useState<DebateSample[]>([]);
  const [analysis, setAnalysis] = useState<DebateAnalysis | null>(null);
  const [tab, setTab] = useState<TabId>("issues");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDebateSamples()
      .then(setSamples)
      .catch(() => setError("サンプルの取得に失敗しました。API を確認してください。"));
  }, []);

  const loadSample = useCallback((sample: DebateSample) => {
    setTopic(sample.topic);
    for (const document of sample.documents) {
      const value = { title: document.title ?? "", text: document.text };
      if (document.side === "pro") setPro(value);
      else setCon(value);
    }
    setAnalysis(null);
    setError(null);
  }, []);

  const runAnalysis = useCallback(async () => {
    const documents = [
      { side: "pro" as const, ...pro },
      { side: "con" as const, ...con },
    ].filter((document) => document.text.trim().length > 0);

    if (documents.length === 0) {
      setError("少なくとも一方の立論を入力してください。");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setAnalysis(await analyzeDebate(documents, topic));
      setTab("issues");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "解析に失敗しました。");
    } finally {
      setLoading(false);
    }
  }, [pro, con, topic]);

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="inline-flex items-center gap-2 text-2xl font-bold tracking-tight">
            <Sparkles className="h-5 w-5 text-slate-500" />
            ディベート立論アナライザー
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            賛否の立論を読み込み、争点ごとの対置（論点マップ）・反駁候補・想定尋問・出典の欠落を自動抽出します。
          </p>
        </div>
        <Link
          href="/"
          className="inline-flex items-center gap-1 rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
        >
          <Calculator className="h-3 w-3" />
          税務調整シミュレーター
        </Link>
      </header>

      <section className="mt-6 space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="flex-1 text-sm">
            <span className="text-slate-600">論題</span>
            <input
              data-testid="topic-input"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="例: 所得税法56条および57条を廃止することの是非"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </label>
          {samples.map((sample) => (
            <button
              key={sample.id}
              data-testid={`load-sample-${sample.id}`}
              onClick={() => loadSample(sample)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              サンプル: {sample.label}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <DocumentInputCard
            side="pro"
            title={pro.title}
            text={pro.text}
            onChange={setPro}
            onError={setError}
          />
          <DocumentInputCard
            side="con"
            title={con.title}
            text={con.text}
            onChange={setCon}
            onError={setError}
          />
        </div>

        <button
          data-testid="run-analysis"
          onClick={runAnalysis}
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          立論を解析
        </button>
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

      {analysis && (
        <section className="mt-8">
          <div className="flex flex-wrap gap-1 border-b border-slate-200 pb-2">
            {TABS.map((item) => (
              <button
                key={item.id}
                data-testid={`tab-${item.id}`}
                onClick={() => setTab(item.id)}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
                  tab === item.id
                    ? "bg-slate-900 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          <div className="mt-4">
            {tab === "issues" && <IssueMap issues={analysis.issues} />}
            {tab === "rebuttals" && <RebuttalList rebuttals={analysis.rebuttals} />}
            {tab === "structure" && (
              <ArgumentTree
                documents={analysis.documents}
                argumentList={analysis.arguments}
              />
            )}
            {tab === "evidence" && (
              <EvidencePanel
                evidence={analysis.evidence}
                argumentList={analysis.arguments}
              />
            )}
          </div>
        </section>
      )}
    </main>
  );
}
