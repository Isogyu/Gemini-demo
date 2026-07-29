"use client";

import { BookOpen } from "lucide-react";

import {
  SIDE_LABEL,
  type Argument,
  type EvidenceReport,
} from "@/lib/debateTypes";

interface Props {
  evidence: EvidenceReport[];
  argumentList: Argument[];
}

function Tags({ label, values }: { label: string; values: string[] }) {
  return (
    <div className="mt-3">
      <p className="text-xs font-medium text-slate-600">
        {label}（{values.length}）
      </p>
      <div className="mt-1 flex flex-wrap gap-1">
        {values.length === 0 ? (
          <span className="text-xs text-slate-400">なし</span>
        ) : (
          values.map((value) => (
            <span
              key={value}
              className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-700"
            >
              {value}
            </span>
          ))
        )}
      </div>
    </div>
  );
}

export function EvidencePanel({ evidence, argumentList }: Props) {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2" data-testid="evidence-panel">
      {evidence.map((report) => {
        const unsupported = argumentList.filter((argument) =>
          report.unsupported_argument_ids.includes(argument.id)
        );
        return (
          <div
            key={report.document_id}
            className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
          >
            <div className="flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-slate-500" />
              <h2 className="text-sm font-semibold text-slate-800">
                {SIDE_LABEL[report.side]}の出典
              </h2>
            </div>
            <Tags label="資料" values={report.materials} />
            <Tags label="法令" values={report.statutes} />
            <Tags label="判例" values={report.cases} />
            <div className="mt-3">
              <p className="text-xs font-medium text-slate-600">
                出典のない論証ブロック（{unsupported.length}）
              </p>
              {unsupported.length === 0 ? (
                <p className="mt-1 text-xs text-slate-400">なし</p>
              ) : (
                <ul className="mt-1 list-disc space-y-1 pl-4 text-xs text-rose-700">
                  {unsupported.map((argument) => (
                    <li key={argument.id}>
                      {argument.section} {argument.heading}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
