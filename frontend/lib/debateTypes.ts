export type Side = "pro" | "con";
export type CitationKind = "material" | "statute" | "case" | "other";
export type ClashStatus = "clash" | "pro_only" | "con_only" | "absent";
export type RebuttalStrength = "high" | "medium" | "low";

export interface Citation {
  raw: string;
  label: string;
  kind: CitationKind;
}

export interface Argument {
  id: string;
  side: Side;
  document_id: string;
  section: string;
  heading: string;
  text: string;
  claim: string;
  citations: Citation[];
  issue_ids: string[];
  warnings: string[];
}

export interface IssueStance {
  side: Side;
  argument_ids: string[];
  points: string[];
  citation_count: number;
}

export interface IssueClash {
  issue_id: string;
  label: string;
  description: string;
  status: ClashStatus;
  pro: IssueStance | null;
  con: IssueStance | null;
  note: string;
}

export interface Rebuttal {
  id: string;
  pattern_id: string;
  target_side: Side;
  issue_id: string;
  issue_label: string;
  title: string;
  body: string;
  trigger: string;
  cross_examination: string[];
  strength: RebuttalStrength;
}

export interface DocumentSummary {
  id: string;
  side: Side;
  title: string;
  char_count: number;
  argument_count: number;
  citation_count: number;
}

export interface EvidenceReport {
  document_id: string;
  side: Side;
  materials: string[];
  statutes: string[];
  cases: string[];
  unsupported_argument_ids: string[];
}

export interface DebateDocumentInput {
  side: Side;
  title?: string;
  text: string;
}

export interface DebateAnalysis {
  topic: string;
  documents: DocumentSummary[];
  arguments: Argument[];
  issues: IssueClash[];
  rebuttals: Rebuttal[];
  evidence: EvidenceReport[];
}

export interface ExtractedDocument {
  title: string;
  text: string;
  detected_side: Side | null;
}

export interface DebateSample {
  id: string;
  label: string;
  topic: string;
  documents: DebateDocumentInput[];
}

export const SIDE_LABEL: Record<Side, string> = {
  pro: "賛成（廃止）側",
  con: "反対（存続）側",
};

export const STATUS_LABEL: Record<ClashStatus, string> = {
  clash: "正面衝突",
  pro_only: "反対側が無応答",
  con_only: "賛成側が無応答",
  absent: "言及なし",
};

export const STRENGTH_LABEL: Record<RebuttalStrength, string> = {
  high: "強",
  medium: "中",
  low: "弱",
};
