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

The corpus is 10 Markdown files with technical notes:

- Python decorators and async/await
- SQL JOINs and PostgreSQL indexing
- Docker Compose
- Git rebase workflows
- Linux file permissions
- REST API design
- CI/CD pipelines
- Web security basics

All files live in `backend/data/raw/`. Swap them out for your own documents and re-run ingestion.

## Setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install llama-index llama-index-embeddings-huggingface llama-index-llms-ollama llama-index-vector-stores-faiss faiss-cpu sentence-transformers fastapi uvicorn pandas ragas datasets
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

## Project layout

```
DomainRAG/
├── backend/
│   ├── app/                # API server and RAG pipeline
│   │   ├── ingestion.py    # Builds the FAISS index
│   │   ├── query_engine.py # Retrieval + LLM generation
│   │   ├── evaluation.py   # RAGAS wrapper
│   │   └── main.py         # FastAPI routes
│   ├── data/raw/           # Your source documents
│   ├── evaluation/         # Test set and experiment runner
│   └── requirements.txt
├── frontend/
│   └── src/                # Next.js app
│       ├── components/     # Chat UI, citation cards, results table
│       └── lib/api.ts      # API client
└── README.md
```