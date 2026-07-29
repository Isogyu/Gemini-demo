"use client";

import { AlertTriangle, ListTree } from "lucide-react";

import {
  SIDE_LABEL,
  type Argument,
  type DocumentSummary,
} from "@/lib/debateTypes";

interface Props {
  documents: DocumentSummary[];
  argumentList: Argument[];
}

export function ArgumentTree({ documents, argumentList }: Props) {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2" data-testid="argument-tree">
      {documents.map((document) => (
        <div
          key={document.id}
          className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
        >
          <div className="flex items-center gap-2">
            <ListTree className="h-4 w-4 text-slate-500" />
            <h2 className="text-sm font-semibold text-slate-800">
              {SIDE_LABEL[document.side]}: {document.title}
            </h2>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            {document.char_count} 字 / 論証ブロック {document.argument_count} 件 / 出典{" "}
            {document.citation_count} 件
          </p>
          <ul className="mt-3 space-y-3">
            {argumentList
              .filter((argument) => argument.document_id === document.id)
              .map((argument) => (
                <li key={argument.id} className="border-l-2 border-slate-200 pl-3">
                  <p className="text-xs font-medium text-slate-500">
                    {argument.section} {argument.heading}
                  </p>
                  <p className="mt-1 text-sm text-slate-800">{argument.claim}</p>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {argument.citations.map((citation) => (
                      <span
                        key={citation.label}
                        className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600"
                      >
                        {citation.label}
                      </span>
                    ))}
                  </div>
                  {argument.warnings.map((warning) => (
                    <p
                      key={warning}
                      className="mt-1 inline-flex items-center gap-1 text-xs text-amber-700"
                    >
                      <AlertTriangle className="h-3 w-3" />
                      {warning}
                    </p>
                  ))}
                </li>
              ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
