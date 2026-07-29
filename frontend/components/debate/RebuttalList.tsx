"use client";

import { MessageSquareQuote, Quote } from "lucide-react";
import { useState } from "react";

import {
  SIDE_LABEL,
  STRENGTH_LABEL,
  type Rebuttal,
  type RebuttalStrength,
  type Side,
} from "@/lib/debateTypes";

const STRENGTH_STYLE: Record<RebuttalStrength, string> = {
  high: "bg-rose-100 text-rose-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-slate-100 text-slate-600",
};

const FILTERS: { id: Side | "all"; label: string }[] = [
  { id: "all", label: "すべて" },
  { id: "con", label: "反対側への反駁" },
  { id: "pro", label: "賛成側への反駁" },
];

export function RebuttalList({ rebuttals }: { rebuttals: Rebuttal[] }) {
  const [filter, setFilter] = useState<Side | "all">("all");
  const visible =
    filter === "all"
      ? rebuttals
      : rebuttals.filter((r) => r.target_side === filter);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="inline-flex items-center gap-2 text-sm font-semibold text-slate-800">
          <MessageSquareQuote className="h-4 w-4 text-slate-500" />
          反駁候補と想定尋問（{visible.length} 件）
        </h2>
        <div className="flex gap-1">
          {FILTERS.map((item) => (
            <button
              key={item.id}
              data-testid={`rebuttal-filter-${item.id}`}
              onClick={() => setFilter(item.id)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium ${
                filter === item.id
                  ? "bg-slate-900 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <ul className="mt-4 space-y-3" data-testid="rebuttal-list">
        {visible.map((rebuttal) => (
          <li
            key={rebuttal.id}
            className="rounded-lg border border-slate-200 p-4"
            data-testid={`rebuttal-${rebuttal.pattern_id}`}
          >
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`rounded px-1.5 py-0.5 text-xs font-medium ${STRENGTH_STYLE[rebuttal.strength]}`}
              >
                反駁力 {STRENGTH_LABEL[rebuttal.strength]}
              </span>
              <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600">
                {SIDE_LABEL[rebuttal.target_side]}への反駁
              </span>
              <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600">
                {rebuttal.issue_label}
              </span>
            </div>
            <h3 className="mt-2 text-sm font-semibold text-slate-900">
              {rebuttal.title}
            </h3>
            <p className="mt-1 text-sm leading-relaxed text-slate-700">
              {rebuttal.body}
            </p>
            <p className="mt-2 inline-flex items-start gap-1 rounded bg-slate-50 px-2 py-1 text-xs text-slate-500">
              <Quote className="mt-0.5 h-3 w-3 shrink-0" />
              起点となった相手の文言: {rebuttal.trigger}
            </p>
            {rebuttal.cross_examination.length > 0 && (
              <div className="mt-3">
                <p className="text-xs font-medium text-slate-600">想定尋問</p>
                <ul className="mt-1 list-decimal space-y-1 pl-5 text-sm text-slate-700">
                  {rebuttal.cross_examination.map((question, index) => (
                    <li key={index}>{question}</li>
                  ))}
                </ul>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
