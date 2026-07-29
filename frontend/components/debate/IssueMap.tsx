"use client";

import { AlertTriangle, Swords } from "lucide-react";

import {
  STATUS_LABEL,
  type ClashStatus,
  type IssueClash,
  type IssueStance,
} from "@/lib/debateTypes";

const STATUS_STYLE: Record<ClashStatus, string> = {
  clash: "bg-slate-100 text-slate-700",
  pro_only: "bg-amber-100 text-amber-800",
  con_only: "bg-amber-100 text-amber-800",
  absent: "bg-slate-100 text-slate-500",
};

function StanceCell({ stance }: { stance: IssueStance | null }) {
  if (!stance) {
    return (
      <td className="align-top px-4 py-3 text-sm text-amber-700">
        <span className="inline-flex items-center gap-1">
          <AlertTriangle className="h-3.5 w-3.5" />
          応答なし
        </span>
      </td>
    );
  }
  return (
    <td className="align-top px-4 py-3 text-sm text-slate-700">
      <ul className="list-disc space-y-1 pl-4">
        {stance.points.map((point, index) => (
          <li key={index}>{point}</li>
        ))}
      </ul>
      <p className="mt-2 text-xs text-slate-500">出典 {stance.citation_count} 件</p>
    </td>
  );
}

export function IssueMap({ issues }: { issues: IssueClash[] }) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-3">
        <Swords className="h-4 w-4 text-slate-500" />
        <h2 className="text-sm font-semibold text-slate-800">論点マップ</h2>
      </div>
      <table className="w-full table-fixed border-collapse" data-testid="issue-map">
        <thead className="bg-slate-50 text-left text-xs text-slate-500">
          <tr>
            <th className="w-52 px-4 py-2 font-medium">争点</th>
            <th className="px-4 py-2 font-medium">賛成（廃止）側</th>
            <th className="px-4 py-2 font-medium">反対（存続）側</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {issues.map((issue) => (
            <tr key={issue.issue_id} data-testid={`issue-${issue.issue_id}`}>
              <td className="align-top px-4 py-3">
                <p className="text-sm font-medium text-slate-800">{issue.label}</p>
                <span
                  className={`mt-1 inline-block rounded px-1.5 py-0.5 text-xs ${STATUS_STYLE[issue.status]}`}
                >
                  {STATUS_LABEL[issue.status]}
                </span>
                <p className="mt-2 text-xs text-slate-500">{issue.description}</p>
              </td>
              <StanceCell stance={issue.pro} />
              <StanceCell stance={issue.con} />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
