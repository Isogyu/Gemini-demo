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

export type StatuteLookupStatus = "found" | "not_found" | "unavailable";
export type MaterialLinkStatus = "linked" | "missing" | "unused";
export type StatuteConsistencyStatus = "consistent" | "differs" | "unverified";

export interface StatuteReference {
  raw: string;
  law_name: string;
  article: number;
  paragraph: number | null;
  label: string;
  cited_by: string[];
}

export interface StatuteArticle {
  label: string;
  law_name: string;
  law_num: string;
  law_id: string;
  article: number;
  paragraph: number | null;
  caption: string;
  text: string;
  source_url: string;
  fetched_at: string | null;
  from_cache: boolean;
  status: StatuteLookupStatus;
  message: string;
  cited_by: string[];
}

export interface MaterialLink {
  number: number;
  label: string;
  sources: string[];
  subsections: string[];
  cited_by: string[];
  status: MaterialLinkStatus;
  note: string;
}

export interface StatuteConsistency {
  label: string;
  packet_text: string;
  status: StatuteConsistencyStatus;
  note: string;
}

export interface ReferenceCheck {
  side: Side;
  packet_title: string;
  material_links: MaterialLink[];
  missing_numbers: number[];
  unused_numbers: number[];
  statute_consistency: StatuteConsistency[];
}

export interface DebateAnalysis {
  topic: string;
  documents: DocumentSummary[];
  arguments: Argument[];
  issues: IssueClash[];
  rebuttals: Rebuttal[];
  evidence: EvidenceReport[];
  statute_references: StatuteReference[];
  statutes: StatuteArticle[];
  reference_checks: ReferenceCheck[];
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
  references: DebateDocumentInput[];
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

export const STATUTE_STATUS_LABEL: Record<StatuteLookupStatus, string> = {
  found: "e-Govより取得",
  not_found: "条文が見つからない",
  unavailable: "e-Gov に接続できません",
};

export const MATERIAL_STATUS_LABEL: Record<MaterialLinkStatus, string> = {
  linked: "紐付け済み",
  missing: "参考資料になし",
  unused: "未使用",
};

export const CONSISTENCY_LABEL: Record<StatuteConsistencyStatus, string> = {
  consistent: "現行条文と一致",
  differs: "現行条文と差異あり",
  unverified: "未照合",
};
