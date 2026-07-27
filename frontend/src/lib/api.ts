const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Citation {
  score: number;
  text: string;
  source: string;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
}

export async function queryQuestion(question: string): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: question }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function healthCheck(): Promise<{ status: string; documents: number }> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}