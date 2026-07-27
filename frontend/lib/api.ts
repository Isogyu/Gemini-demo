import type {
  ReconciliationRequest,
  ReconciliationResult,
  SampleDataset,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export function fetchSamples(): Promise<SampleDataset[]> {
  return request<SampleDataset[]>("/api/samples");
}

export function postReconciliation(
  payload: ReconciliationRequest
): Promise<ReconciliationResult> {
  return request<ReconciliationResult>("/api/reconciliation", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
