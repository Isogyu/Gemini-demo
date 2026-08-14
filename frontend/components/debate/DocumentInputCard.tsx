"use client";

import { AlertTriangle, FileUp, Loader2 } from "lucide-react";
import { useRef, useState } from "react";

import { extractDebateDocument } from "@/lib/debateApi";
import { SIDE_LABEL, type Side } from "@/lib/debateTypes";

type DocumentKind = "argument" | "reference";

interface Props {
  side: Side;
  title: string;
  text: string;
  kind?: DocumentKind;
  onChange: (value: { title: string; text: string }) => void;
  onError: (message: string) => void;
}

const KIND_LABEL: Record<DocumentKind, string> = {
  argument: "立論",
  reference: "参考資料（任意）",
};

const PLACEHOLDER: Record<DocumentKind, string> = {
  argument:
    "「Ⅰ. 主張」「1. 理由」「（1）公平」のような見出しを含む立論を貼り付けてください。",
  reference:
    "「Ⅰ. 関連法令」「Ⅱ. 資料」を含む参考資料を貼り付けてください。資料番号と出典文献を立論の【資料N参照】に突合します。",
};

export function DocumentInputCard({
  side,
  title,
  text,
  kind = "argument",
  onChange,
  onError,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [warning, setWarning] = useState<string | null>(null);

  const accent =
    side === "pro"
      ? "border-emerald-200 bg-emerald-50/40"
      : "border-indigo-200 bg-indigo-50/40";

  async function handleFile(file: File) {
    setUploading(true);
    setWarning(null);
    try {
      const extracted = await extractDebateDocument(file);
      onChange({ title: extracted.title, text: extracted.text });
      if (extracted.detected_side && extracted.detected_side !== side) {
        setWarning(
          `「${file.name}」は${SIDE_LABEL[extracted.detected_side]}の資料と推定されます。枠を確認してください。`
        );
      }
    } catch (error) {
      onError(error instanceof Error ? error.message : "ファイルの読み取りに失敗しました");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div className={`rounded-xl border p-4 shadow-sm ${accent}`}>
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-slate-800">
          {SIDE_LABEL[side]}の{KIND_LABEL[kind]}
        </h2>
        <button
          type="button"
          data-testid={`upload-${kind}-${side}`}
          onClick={() => inputRef.current?.click()}
          className="inline-flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
        >
          {uploading ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <FileUp className="h-3 w-3" />
          )}
          .docx / .txt を読み込む
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".docx,.txt,.md"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleFile(file);
          }}
        />
      </div>

      {warning && (
        <div
          data-testid={`mismatch-${kind}-${side}`}
          className="mt-3 flex items-start gap-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800"
        >
          <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
          <span>{warning}</span>
        </div>
      )}

      <input
        data-testid={`title-${kind}-${side}`}
        value={title}
        onChange={(e) => onChange({ title: e.target.value, text })}
        placeholder="タイトル（任意）"
        className="mt-3 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
      />
      <textarea
        data-testid={`text-${kind}-${side}`}
        value={text}
        onChange={(e) => {
          setWarning(null);
          onChange({ title, text: e.target.value });
        }}
        rows={kind === "argument" ? 10 : 6}
        placeholder={PLACEHOLDER[kind]}
        className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-xs leading-relaxed"
      />
      <p className="mt-1 text-right text-xs text-slate-500">{text.length} 字</p>
    </div>
  );
}
