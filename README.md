# DomainRAG

A RAG assistant that answers questions from a curated tech knowledge base, shows citations, and measures its own performance with RAGAS.

---

## Architecture

```
Next.js frontend → FastAPI backend → LlamaIndex → FAISS vector store
                                              → Ollama (Llama 3.2)
                                              → RAGAS evaluation
```

The frontend sends your question to the backend. LlamaIndex finds relevant chunks from the FAISS index, passes them as context to the local LLM, and returns an answer with source citations. The evaluation pipeline runs RAGAS across different configurations to compare retrieval quality.

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
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

You also need Ollama with the llama3.2 model:

```bash
ollama pull llama3.2
```

Build the vector index and start the API:

```bash
PYTHONPATH=. python -m app.ingestion
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

The response includes an answer and citations with relevance scores and source filenames.

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
source .venv/bin/activate
PYTHONPATH=. python evaluation/run_experiments.py
```

Results land in `backend/evaluation/results/` as both CSV and JSON.

Preliminary latency results (15 questions, 15 queries per config):

| Config | Chunk size | Overlap | Top-K | Avg latency |
|--------|-----------|---------|-------|-------------|
| A (baseline) | 512 | 128 | 3 | 3.67s |
| B (large chunks) | 1024 | 256 | 5 | 4.36s |
| C (more docs) | 512 | 128 | 5 | 4.15s |

Baseline (smaller chunks, fewer docs) is the fastest. Config C retrieves more context with minimal latency increase.

### RAGAS metrics

Scored against 15 test questions using the local Llama 3.2 model. Faithfulness requires JSON-structured output from the scoring LLM which small local models may not produce reliably, resulting in NaN.

| Metric | A (baseline) | B (large chunks) | C (more docs) |
|--------|-------------|-----------------|--------------|
| Answer relevancy | 0.85 | 0.82 | 0.87 |
| Context recall | 0.75 | 0.80 | 0.78 |
| Context precision | 0.50 | 0.55 | 0.60 |
| Avg latency (s) | 3.67 | 4.36 | 4.15 |

Config C (smaller chunks, more documents retrieved) offers the best balance of relevancy and precision with reasonable latency.

## Limitations

- **Faithfulness metric scores NaN**: RAGAS faithfulness requires the scoring LLM to emit structured JSON. Small local models like Llama 3.2 (8B) often produce unparseable output. Swap in a stronger model (GPT-4, Llama 70B) for accurate faithfulness measurements.
- **Local-only LLM**: All inference runs on a single local machine. Latency (~3–4s per query) and quality are constrained by the 8B parameter model. No cloud LLM fallback is configured.
- **Small corpus**: 14 documents spanning broad topics. Retrieval quality and citation diversity would improve with a larger, more focused domain corpus.
- **No persistent database**: The system has no relational database. Authentication is limited to a static API key — no user registration, MFA, or session management.
- **Evaluation scope**: 15 test questions. A larger test set would yield more statistically significant metric comparisons.

## Future work

- Swap eval LLM to a larger model (Llama 70B via Ollama, or GPT-4o via API) to get valid faithfulness scores.
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
│   │   ├── models.py       # Pydantic request/response schemas
│   │   ├── query_engine.py # Retrieval + LLM generation + circuit breaker
│   │   └── main.py         # FastAPI routes, rate limiting, error handling
│   ├── data/raw/           # Source documents (14 Markdown files)
│   ├── evaluation/         # Test set and experiment runner
│   └── requirements.txt    # Pinned Python dependencies
├── frontend/
│   └── src/                # Next.js app
│       ├── components/     # Chat UI, citation cards, results table
│       └── lib/api.ts      # API client
└── README.md
```