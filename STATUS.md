# DomainRAG — STATUS

Last updated: 2026-09-04

## What was done till now

### Core project (complete, verified)
- RAG assistant: Next.js frontend -> FastAPI backend -> LlamaIndex -> FAISS -> Ollama, with RAGAS evaluation.
- 14-document curated tech corpus (SQL, Python, Docker, git, Linux, REST, CI/CD, security, architecture).
- Document upload (+10MB/pdf/docx/etc.), web scraping with SSRF guard, Notes tab (localStorage).
- Runtime model switching: local Ollama models + OpenAI-compatible providers (OpenAI, Groq, OpenRouter, OpenCode Zen, custom) with automatic fallback to the local model.
- Streaming answers (`/query/stream` SSE), citations with similarity scores + footnote markers, MIN_SIMILARITY relevance floor (0.62).
- Optional API-key auth (constant-time compare), sliding-window rate limiting, Pydantic validation, global error handler, structured JSON logging, LLM circuit breaker (3 failures / 60s reset).
- RAGAS evaluation: 3 configurations (A: 512/128/3, B: 1024/256/5, C: 512/128/5), 15-question test set, JSON-format eval LLM; results in `backend/evaluation/results/`.
- Verified live (2026-09-04): index built with 31 documents; backend boots; `/health` ok; `/query` returns correct answers with citations; Ollama (qwen3:8b, qwen2.5:7b) serving.

### Local uncommitted improvements (committed with this push)
- `backend/app/config.py`: `LLM_CONTEXT_WINDOW` env var (default 8192) — caps the KV cache so local inference stays on the GPU.
- `backend/app/ingestion.py`: set `Settings.transformations` explicitly (stale default parser could skip chunking on server-process rebuilds); use `llama_index.core` import path.
- `backend/app/model_registry.py`: wire the context-window cap into the local LLM config.
- `backend/tests/verify_pipeline.py`: fallback e2e now exercises the OpenCode Zen provider path.
- `.opencode/`: local agent skills.

### JARTRON agent run (2026-09-04) — COMPLETED
- JARTRON (the local agent app) completed the project: verify suite 76/76, backend tests, frontend lint/build/boot, reduced evaluation (config A, 5-question set — real numbers: relevancy 0.964, recall 1.0, precision 1.0, latency 2.15s), README updated, committed as `2c8f293` and pushed.
- Agent's top-5 improvements: (1) fix faithfulness-eval reliability (timeouts vs qwen2.5:7b), (2) resumable/parameterized experiment runner, (3) cache the embedding model, (4) parallelize RAGAS jobs, (5) per-sample score reporting.

## What to do next

1. **Full evaluation run**: the reduced config-A run succeeded; run the full A/B/C comparison after applying the agent's reliability fixes (bump EVAL timeout / num_ctx or use a remote eval LLM; resumable runner; parallel judgement jobs).
2. **Frontend polish**: run `npm run lint`/`build` and fix any warnings; add the screenshots mentioned in README "Future work" (chat UI with citations, results table).
3. **Recommended improvements** (from the JARTRON QA session):
   - Expand the corpus + test set (50 docs / 100 Q&A) for statistically meaningful RAGAS metrics.
   - Swap the eval LLM to a larger model (Llama 70B / a cloud model) for better faithfulness judgments.
   - Add persistent chat history (SQLite) and JWT auth with scoped keys.
   - CI: dependency scanning (pip-audit / Dependabot), SBOM, lint+test gate.
   - Deploy behind a reverse proxy (Caddy/Nginx + Let's Encrypt) for HTTPS.
   - Add prompt-injection guardrails on uploaded/scraped content.
4. **When done**: update README numbers if they changed, commit, push.