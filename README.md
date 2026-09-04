# DomainRAG

A RAG assistant that answers questions from a curated tech knowledge base, shows citations, and measures its own performance with RAGAS.

---

## Architecture

```
Next.js frontend → FastAPI backend → LlamaIndex → FAISS vector store
                                              → Ollama (Qwen 3 8B + Qwen 2.5)
                                              → RAGAS evaluation
```

The frontend sends your question to the backend. LlamaIndex finds relevant chunks from the FAISS index, passes them as context to the local LLM, and returns an answer with source citations. The evaluation pipeline runs RAGAS across different configurations to compare retrieval quality. You can upload your own documents from the UI, and switch the answer model between local Ollama models and OpenAI-compatible providers (OpenAI, Groq, OpenRouter, OpenCode Zen, or a custom endpoint) from the model settings modal — if a cloud provider fails, the backend automatically falls back to the local model. A **Notes** tab (next to Ask) keeps study notes saved in your browser's local storage.

## What it knows

The corpus is 14 Markdown files covering:

- Python decorators and async/await
- SQL JOINs and PostgreSQL indexing
- Docker Compose
- Git rebase workflows
- Linux file permissions
- REST API design
- CI/CD pipelines
- Web security and production security
- Architecture and scaling patterns
- Traffic and reliability patterns
- Production deployment checklist

All files live in `backend/data/raw/`. Swap them out for your own documents and re-run ingestion.

## Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

You also need Ollama with the chat model (qwen3:8b) and the evaluation model (qwen2.5:7b):

```bash
ollama pull qwen3:8b
ollama pull qwen2.5:7b
```

Ollama models are stored in `~/dev/models/ollama` (set via `OLLAMA_MODELS`). A user-level systemd service (`~/.config/systemd/user/ollama.service`) keeps Ollama running with that location.

Build the vector index:

```bash
PYTHONPATH=. ./venv/bin/python -m app.ingestion
```

Start the API:

```bash
# Option A: Use venv binary directly
PYTHONPATH=. ./venv/bin/uvicorn app.main:app --reload --port 8000

# Option B: Activate the venv first
source venv/bin/activate
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

The API runs on http://localhost:8000. Check it with `curl http://localhost:8000/health`.

### Frontend

```bash
cd frontend
npm install
npx shadcn@latest add button card input scroll-area separator table -y
npm run dev
```

Open http://localhost:3000.

## Using the API

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is a LEFT JOIN in SQL?"}'
```

The response includes an answer and citations with relevance scores and source filenames. Streaming variant at `/query/stream` (Server-Sent Events: thinking steps, citations, then answer tokens).

### Uploading documents

From the UI, click the **+** icon next to the input box to add your own files. Supported types: `.md`, `.txt`, `.rst`, `.pdf`, `.html`, `.htm`, `.csv`, `.json`, `.yaml`, `.yml`, `.docx`, `.pptx`, `.xlsx` (up to 10 MB each, 10 per request). Uploaded files are stored in `backend/data/raw/`, the index is rebuilt, and answers immediately include them. Programmatically:

```bash
curl -X POST http://localhost:8000/documents -F "files=@my-notes.md"
```

### Querying

Retrieval enforces a relevance floor (`MIN_SIMILARITY`, default `0.62`, env `DOMAINRAG_MIN_SIMILARITY`): chunks scoring below it are never passed to the model as context. If nothing clears the floor, the assistant says so instead of guessing. Sources show the chunk similarity score, and answers cite them with footnote markers.

### Scraping web pages

Click the **globe** icon next to the input box to ingest a web page into the knowledge base. The page is fetched, stripped to its readable content, saved as markdown in `backend/data/scraped/`, and the index is rebuilt. Up to 10 pages can be crawled per request — with `max_pages > 1`, additional pages are followed breadth-first on the same domain. Scraped citations link back to the original URL.

```bash
curl -X POST http://localhost:8000/ingest/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://docs.python.org/3/library/asyncio.html", "max_pages": 3}'
```

Scraping is protected against SSRF: private/loopback/link-local addresses (e.g. `localhost`, `192.168.x.x`) are rejected. Timeout and user-agent are configurable via `SCRAPE_TIMEOUT` and `SCRAPE_USER_AGENT`.

### Switching models

Open the **model settings** (gear icon in the header) to:
- Pick any model already installed in local Ollama
- Connect an OpenAI-compatible provider with an API key — the key is validated against the provider, held in memory only, and never persisted or returned
- Providers: **Groq** (free tier: Llama 3.3 70B, DeepSeek R1 Distill 70B, Qwen QWQ), **OpenRouter** (free `:free` models), **OpenCode Zen** (free models incl. `deepseek-v4-flash-free`, `big-pickle`, `nemotron-3-ultra-free` — the same models used by the OpenCode CLI; get a key at https://opencode.ai/auth), OpenAI, or any custom OpenAI-compatible base URL
- Reset back to the local default

**Automatic fallback**: if the active cloud provider fails at run time (dead API key, retired model slug, rate limit), the backend transparently retries the question with the local model and marks the config with `fallback_active` so the UI shows a warning. Both the plain `/query` and the streaming `/query/stream` paths do this.

You can also boot the backend with a cloud provider from the environment (`DOMAINRAG_PROVIDER`, `DOMAINRAG_MODEL`, `DOMAINRAG_PROVIDER_API_KEY`, `DOMAINRAG_BASE_URL`); it is applied without validation and falls back to the local model automatically if it fails.

API: `GET /models` (current config, installed local models, provider options), `POST /models` (apply `{"provider", "model", "api_key", "base_url"}`), `POST /models/reset`.

### API key auth (optional)

Set the `DOMAINRAG_API_KEY` environment variable to enable API key authentication:

```bash
DOMAINRAG_API_KEY=my-secret-key PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

Requests must then include the `x-api-key` header:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "x-api-key: my-secret-key" \
  -d '{"query": "What is a LEFT JOIN in SQL?"}'
```

## Running experiments

Three configurations are compared:

| Config | Chunk size | Overlap | Top-K |
|--------|-----------|---------|-------|
| A (baseline) | 512 | 128 | 3 |
| B (large chunks) | 1024 | 256 | 5 |
| C (more docs) | 512 | 128 | 5 |

Run them all at once:

```bash
cd backend
source venv/bin/activate
PYTHONPATH=. python evaluation/run_experiments.py
```

The eval LLM defaults to `qwen2.5:7b` and can be overridden with the `EVAL_MODEL` environment variable.

Results land in `backend/evaluation/results/` as both CSV and JSON.

Latency results (config A only — the full 3-config/15-question run exceeded ~15 min, so results were regenerated with a reduced 5-question set; Qwen 3 8B):

| Config | Chunk size | Overlap | Top-K | Avg latency |
|--------|-----------|---------|-------|-------------|
| A (baseline) | 512 | 128 | 3 | 2.15s |

Each config builds its own index with its own chunk settings and retrieval depth, so differences reflect the actual configuration.

### RAGAS metrics

Scored against 5 test questions (reduced set; see Limitations). The eval LLM (`qwen2.5:7b`) runs with `format="json"`. Ground-truth contexts are the full source documents referenced by the test set, and the eval LLM can be overridden via `EVAL_MODEL`.

| Metric | A (baseline) |
|--------|-------------|
| Faithfulness | n/a (eval LLM timeouts) |
| Answer relevancy | 0.964 |
| Context recall | 1.000 |
| Context precision | 1.000 |
| Avg latency (s) | 2.15 |

Faithfulness could not be computed because several RAGAS judgement jobs timed out against the local eval LLM; the other metrics produced valid scores. Context recall/precision are 1.0 because ground-truth contexts are the full source documents, making retrieval from the same corpus trivially complete — treat them as upper bounds.

## Limitations

- **Local-only LLM**: All inference runs on a single local machine (Qwen 3 8B on an 8GB GPU, ~5–7s per query). Quality is constrained by the local model; cloud models can be added via the model settings with a provider API key.
- **Small corpus**: 14 documents spanning broad topics. Retrieval quality and citation diversity would improve with a larger, more focused domain corpus.
- **No persistent database**: The system has no relational database. Authentication is limited to a static API key — no user registration, MFA, or session management.
- **Evaluation scope**: The last run captured only config A with 5 questions (full run exceeded ~15 min and RAGAS faithfulness jobs timed out). Results in `backend/evaluation/results/` are marked `reduced`. A larger test set and a faster/remote eval LLM would yield statistically significant metric comparisons.

## Future work

- Swap eval LLM to a larger model (Llama 70B via Ollama, or GPT-4o via API) for higher-quality faithfulness judgments.
- Add user registration with JWT-based auth, refresh tokens, and scoped API keys.
- Deploy behind Nginx/Caddy with automatic HTTPS via Let's Encrypt.
- Add persistent chat history with a lightweight database (SQLite for single-user, PostgreSQL for multi-user).
- Expand the corpus and test set to at least 50 documents and 100 Q&A pairs.
- Add prompt injection guardrails and output content filtering.
- Generate a software bill of materials and add CI dependency scanning (pip-audit, Dependabot).
- Take screenshots of the chat UI with citations and the experiment results table for the README.

## Security

The following controls are implemented:

- **Authentication**: Optional API key authentication via the `x-api-key` header. Uses constant-time comparison (`hmac.compare_digest`) to prevent timing attacks. Auth is enforced through FastAPI middleware on all endpoints except `/health`, `/docs`, and `/openapi.json`.
- **Rate limiting**: Sliding-window rate limiter at 30 requests per 60-second window per IP address. Configured via `RATE_LIMIT_WINDOW` and `RATE_LIMIT_MAX` in `config.py`.
- **Input validation**: All inputs validated via Pydantic schemas — query length constrained to 1–2000 characters. Rejected inputs return 422 with detail.
- **Error handling**: Global exception handler catches unhandled errors and returns generic `500 Internal server error` responses — no stack traces or internal details are exposed. Streaming endpoint wraps retrieval and generation in try/except blocks with structured error events.
- **Logging**: All requests are logged as structured JSON with timestamp, method, path, status code, elapsed time, and anonymized user ID. Authentication attempts and rate-limit violations are explicitly logged.
- **Secrets management**: API key and configuration loaded from environment variables (`DOMAINRAG_API_KEY`) — never hardcoded or committed.
- **Dependency pinning**: All Python dependencies pinned to exact versions in `requirements.txt`. Lockfile can be generated with `pip freeze`.
- **Circuit breaker**: LLM/Ollama calls are protected by a circuit breaker that opens after 3 failures with a 60-second reset timeout. Prevents cascading failures when the LLM is unavailable.

### Checklist coverage

| Practice | Status |
|----------|--------|
| Authentication & sessions | Optional API key auth, stateless |
| Authorization & data access | Middleware-enforced API key check |
| Secrets & configuration | Environment variables only |
| Input validation & output encoding | Pydantic validation, parameterized queries (LlamaIndex) |
| Transport & storage security | HTTPS assumed (reverse proxy), no sensitive data stored |
| Dependency & supply chain | Pinned versions in requirements.txt |
| Logging & monitoring | Structured JSON logs with request ID, auth events |
| Error handling | Generic error messages, global exception handler |
| Rate limiting | Sliding window, 30 req/min per IP |
| Circuit breaker | 3-failure threshold, 60s reset |
| Graceful degradation | Streaming endpoint isolates retrieval & generation errors |

## Operations

### Logging

Logs are emitted as newline-delimited JSON (`application/json` format) to stdout. Each log entry contains:

- `timestamp` — ISO 8601 UTC
- `level` — INFO, WARNING, ERROR
- `logger` — source module name
- `message` — human-readable summary
- `method` / `path` / `status` / `elapsed_ms` — request metadata (on request logs)
- `client_ip` — on rate-limit violations and error events
- `user_id` — truncated API key prefix (when auth is enabled)

### Monitoring assumptions

- Health check endpoint (`GET /health`) returns document count and `{"status": "ok"}` — suitable for load balancer probes.
- Rate-limit violations and 5xx errors are logged at WARNING and ERROR levels respectively, making them actionable via log-based alerting.
- Structured logs can be forwarded to any log aggregation service (e.g., Loki, Elasticsearch, CloudWatch) for dashboarding and alerting.

### Scaling assumptions

- **Stateless app servers**: No server-side session state. Auth is stateless (API key per request). Horizontal scaling requires only a shared FAISS index file (read-only after build) and a load balancer.
- **Database**: No relational database used. The FAISS vector index is built once and loaded read-only at startup.
- **Reverse proxy**: Assumes HTTPS termination via Nginx, Caddy, or similar in production. The application does not handle TLS itself.
- **Connection pooling**: Not applicable (no relational DB). For the vector store, FAISS is single-process; use a shared filesystem (NFS, S3) if distributing the index across replicas.

## Project layout

```
DomainRAG/
├── backend/
│   ├── app/                # API server and RAG pipeline
│   │   ├── auth.py         # API key authentication middleware
│   │   ├── config.py       # Configuration and security settings
│   │   ├── ingestion.py    # Builds the FAISS index
│   │   ├── logger.py       # Structured JSON logger
│   │   ├── main.py         # FastAPI routes, rate limiting, error handling
│   │   ├── model_registry.py # Runtime model switching (local + cloud providers)
│   │   ├── models.py       # Pydantic request/response schemas
│   │   ├── query_engine.py # Retrieval + LLM generation + circuit breaker
│   │   ├── scraper.py      # Web scraping: fetch, extract, save as markdown
│   │   └── uploads.py      # Document upload validation and storage
│   ├── data/raw/           # Source documents (14 Markdown files + uploads)
│   ├── data/scraped/       # Pages ingested via the web scraper
│   ├── evaluation/         # Test set and experiment runner
│   └── requirements.txt    # Pinned Python dependencies
├── frontend/
│   └── src/                # Next.js app
│       ├── components/     # Chat UI, citation cards, settings + scrape modals
│       └── lib/api.ts      # API client
└── README.md
```