import type {
  DebateAnalysis,
  DebateDocumentInput,
  DebateSample,
  ExtractedDocument,
} from "./debateTypes";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function parseError(response: Response): Promise<never> {
  let detail = `API request failed: ${response.status}`;
  try {
    const body = (await response.json()) as { detail?: string };
    if (body.detail) detail = body.detail;
  } catch {
    // レスポンスが JSON でない場合はステータスのみを返す
  }
  throw new Error(detail);
}

export async function fetchDebateSamples(): Promise<DebateSample[]> {
  const response = await fetch(`${API_BASE_URL}/api/debate/samples`, {
    cache: "no-store",
  });
  if (!response.ok) return parseError(response);
  return (await response.json()) as DebateSample[];
}

export async function analyzeDebate(
  documents: DebateDocumentInput[],
  topic: string,
  references: DebateDocumentInput[] = []
): Promise<DebateAnalysis> {
  const response = await fetch(`${API_BASE_URL}/api/debate/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ documents, references, topic }),
    cache: "no-store",
  });
  if (!response.ok) return parseError(response);
  return (await response.json()) as DebateAnalysis;
}

export async function extractDebateDocument(
  file: File
): Promise<ExtractedDocument> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_BASE_URL}/api/debate/extract`, {
    method: "POST",
    body: form,
  });
  if (!response.ok) return parseError(response);
  return (await response.json()) as ExtractedDocument;
}
