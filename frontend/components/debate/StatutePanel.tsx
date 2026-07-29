"use client";

import { ExternalLink, Landmark, Link2 } from "lucide-react";

import {
  CONSISTENCY_LABEL,
  MATERIAL_STATUS_LABEL,
  SIDE_LABEL,
  STATUTE_STATUS_LABEL,
  type MaterialLinkStatus,
  type ReferenceCheck,
  type StatuteArticle,
  type StatuteConsistencyStatus,
  type StatuteLookupStatus,
  type StatuteReference,
} from "@/lib/debateTypes";

interface Props {
  references: StatuteReference[];
  statutes: StatuteArticle[];
  checks: ReferenceCheck[];
}

const STATUTE_BADGE: Record<StatuteLookupStatus, string> = {
  found: "bg-emerald-100 text-emerald-800",
  not_found: "bg-rose-100 text-rose-800",
  unavailable: "bg-amber-100 text-amber-800",
};

const MATERIAL_BADGE: Record<MaterialLinkStatus, string> = {
  linked: "bg-emerald-100 text-emerald-800",
  missing: "bg-rose-100 text-rose-800",
  unused: "bg-amber-100 text-amber-800",
};

const CONSISTENCY_BADGE: Record<StatuteConsistencyStatus, string> = {
  consistent: "bg-emerald-100 text-emerald-800",
  differs: "bg-rose-100 text-rose-800",
  unverified: "bg-slate-100 text-slate-600",
};

export function StatutePanel({ references, statutes, checks }: Props) {
  const byLabel = new Map(statutes.map((statute) => [statute.label, statute]));

  return (
    <div className="space-y-4" data-testid="statute-panel">
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-center gap-2">
          <Landmark className="h-4 w-4 text-slate-500" />
          <h2 className="text-sm font-semibold text-slate-800">
            引用された法令の現行条文（e-Gov 法令API）
          </h2>
          <span className="text-xs text-slate-500">
            {references.length} 件を抽出 / {statutes.length} 件を照会
          </span>
        </div>

        {references.length === 0 ? (
          <p className="mt-3 text-xs text-slate-400">
            立論・参考資料から法令の引用を検出できませんでした。
          </p>
        ) : (
          <ul className="mt-3 space-y-3">
            {references.map((reference) => {
              const statute = byLabel.get(reference.label);
              const status = statute?.status ?? "unavailable";
              return (
                <li
                  key={reference.label}
                  className="rounded-lg border border-slate-200 p-3"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-semibold text-slate-800">
                      {reference.label}
                    </span>
                    <span
                      className={`rounded px-1.5 py-0.5 text-xs ${STATUTE_BADGE[status]}`}
                    >
                      {STATUTE_STATUS_LABEL[status]}
                    </span>
                    {statute?.from_cache && (
                      <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600">
                        キャッシュ
                      </span>
                    )}
                    {statute?.caption && (
                      <span className="text-xs text-slate-500">
                        {statute.caption}
                      </span>
                    )}
                    {statute?.source_url && (
                      <a
                        href={statute.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="ml-auto inline-flex items-center gap-1 text-xs text-sky-700 hover:underline"
                      >
                        e-Gov で開く
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                  {statute?.text ? (
                    <p className="mt-2 whitespace-pre-wrap text-xs leading-relaxed text-slate-700">
                      {statute.text}
                    </p>
                  ) : (
                    <p className="mt-2 text-xs text-rose-700">
                      {statute?.message || "条文を取得できませんでした"}
                    </p>
                  )}
                  {reference.cited_by.length > 0 && (
                    <p className="mt-2 text-xs text-slate-500">
                      引用元: {reference.cited_by.join(", ")}
                    </p>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {checks.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-4 text-xs text-slate-500">
          参考資料をアップロードすると、【資料N参照】と資料番号・出典文献の突合結果を表示します。
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {checks.map((check) => (
            <div
              key={`${check.side}-${check.packet_title}`}
              className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
              data-testid={`reference-check-${check.side}`}
            >
              <div className="flex items-center gap-2">
                <Link2 className="h-4 w-4 text-slate-500" />
                <h2 className="text-sm font-semibold text-slate-800">
                  {SIDE_LABEL[check.side]}の参考資料の突合
                </h2>
              </div>
              <p className="mt-1 text-xs text-slate-500">
                {check.packet_title || "（タイトルなし）"}
              </p>

              {(check.missing_numbers.length > 0 ||
                check.unused_numbers.length > 0) && (
                <ul className="mt-2 space-y-1 text-xs">
                  {check.missing_numbers.length > 0 && (
                    <li className="rounded bg-rose-50 px-2 py-1 text-rose-800">
                      参考資料に存在しない資料番号の引用:{" "}
                      {check.missing_numbers.map((n) => `資料${n}`).join("、")}
                    </li>
                  )}
                  {check.unused_numbers.length > 0 && (
                    <li className="rounded bg-amber-50 px-2 py-1 text-amber-800">
                      一度も引用されていない資料:{" "}
                      {check.unused_numbers.map((n) => `資料${n}`).join("、")}
                    </li>
                  )}
                </ul>
              )}

              <p className="mt-3 text-xs font-medium text-slate-600">
                資料の紐付け（{check.material_links.length}）
              </p>
              <ul className="mt-1 space-y-2">
                {check.material_links.map((link) => (
                  <li key={link.number} className="text-xs">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium text-slate-800">
                        資料{link.number}
                      </span>
                      <span
                        className={`rounded px-1.5 py-0.5 ${MATERIAL_BADGE[link.status]}`}
                      >
                        {MATERIAL_STATUS_LABEL[link.status]}
                      </span>
                      <span className="text-slate-600">{link.label}</span>
                    </div>
                    {link.sources.length > 0 && (
                      <p className="mt-0.5 text-slate-500">
                        出典: {link.sources.join(" / ")}
                      </p>
                    )}
                    {link.cited_by.length > 0 && (
                      <p className="mt-0.5 text-slate-500">
                        引用元: {link.cited_by.join(", ")}
                      </p>
                    )}
                    {link.note && (
                      <p className="mt-0.5 text-rose-700">{link.note}</p>
                    )}
                  </li>
                ))}
              </ul>

              <p className="mt-3 text-xs font-medium text-slate-600">
                条文の照合（{check.statute_consistency.length}）
              </p>
              <ul className="mt-1 space-y-1">
                {check.statute_consistency.length === 0 ? (
                  <li className="text-xs text-slate-400">なし</li>
                ) : (
                  check.statute_consistency.map((entry) => (
                    <li
                      key={entry.label}
                      className="flex flex-wrap items-center gap-2 text-xs"
                    >
                      <span className="text-slate-800">{entry.label}</span>
                      <span
                        className={`rounded px-1.5 py-0.5 ${CONSISTENCY_BADGE[entry.status]}`}
                      >
                        {CONSISTENCY_LABEL[entry.status]}
                      </span>
                      <span className="text-slate-500">{entry.note}</span>
                    </li>
                  ))
                )}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
