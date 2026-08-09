const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Citation {
  score: number;
  text: string;
  source: string;
  url: string;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
}

export interface ModelStatus {
  provider: string;
  model: string;
  base_url: string;
  using_local: boolean;
  fallback_active: boolean;
}

export interface ProviderInfo {
  label: string;
  base_url: string;
  models: string[];
}

export interface ModelsResponse {
  current: ModelStatus;
  local: string[];
  providers: Record<string, ProviderInfo>;
}

export interface UploadResponse {
  uploaded: string[];
  skipped: { name: string; reason: string }[];
  documents: number;
}

export interface ScrapeResponse {
  saved: string[];
  skipped: { url: string; reason: string }[];
  pages: number;
  documents: number;
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `API error: ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* keep default */
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function queryQuestion(question: string): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: question }),
  });
  return handle<QueryResponse>(res);
}

export interface StreamHandlers {
  onThinking: (step: string) => void;
  onCitations: (citations: Citation[]) => void;
  onToken: (token: string) => void;
  onDone: (answer: string) => void;
  onError: (detail: string) => void;
}

export async function streamQuery(
  question: string,
  handlers: StreamHandlers
): Promise<void> {
  const res = await fetch(`${API_BASE}/query/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: question }),
  });
  if (!res.ok || !res.body) {
    let detail = `API error: ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* keep default */
    }
    handlers.onError(detail);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";
    for (const evt of events) {
      let type = "";
      let data = "";
      for (const line of evt.split("\n")) {
        if (line.startsWith("event:")) type = line.slice(6).trim();
        else if (line.startsWith("data:")) data = line.slice(5).trim();
      }
      if (!type || !data) continue;
      const payload = JSON.parse(data);
      switch (type) {
        case "thinking":
          handlers.onThinking(payload.step);
          break;
        case "citations":
          handlers.onCitations(payload as Citation[]);
          break;
        case "token":
          handlers.onToken(payload.text);
          break;
        case "done":
          handlers.onDone(payload.answer);
          break;
        case "error":
          handlers.onError(payload.detail);
          break;
      }
    }
  }
}

export async function healthCheck(): Promise<{ status: string; documents: number }> {
  const res = await fetch(`${API_BASE}/health`);
  return handle(res);
}

export async function getModels(): Promise<ModelsResponse> {
  const res = await fetch(`${API_BASE}/models`);
  return handle<ModelsResponse>(res);
}

export async function setModel(cfg: {
  provider: string;
  model: string;
  api_key?: string;
  base_url?: string;
}): Promise<ModelStatus> {
  const res = await fetch(`${API_BASE}/models`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cfg),
  });
  return handle<ModelStatus>(res);
}

export async function resetModel(): Promise<ModelStatus> {
  const res = await fetch(`${API_BASE}/models/reset`, { method: "POST" });
  return handle<ModelStatus>(res);
}

export async function uploadDocuments(files: File[]): Promise<UploadResponse> {
  const form = new FormData();
  for (const f of files) form.append("files", f);
  const res = await fetch(`${API_BASE}/documents`, { method: "POST", body: form });
  return handle<UploadResponse>(res);
}

export async function scrapeUrl(url: string, maxPages = 1): Promise<ScrapeResponse> {
  const res = await fetch(`${API_BASE}/ingest/url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, max_pages: maxPages }),
  });
  return handle<ScrapeResponse>(res);
}
