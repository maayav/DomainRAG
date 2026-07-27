# DomainRAG

Domain-specific RAG assistant with LlamaIndex, FAISS, Ollama, and RAGAS evaluation.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (Next.js + Tailwind + shadcn/ui + assistant-ui)       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Chat Interface → fetch(/api/query) → Display Citations  │    │
│  └──────────────────────────┬──────────────────────────────┘    │
│                              │ POST /query                       │
│                              ▼                                  │
│  Backend (FastAPI + LlamaIndex + FAISS + Ollama)                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  /query → Retrieval → Ollama LLM → Answer + Citations    │    │
│  │  /ingest → Load Docs → Chunk → Embed → FAISS Index      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  Evaluation (RAGAS)                                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Test Set (15 Q&A) → RAGAS → Faithfulness, Relevancy,    │    │
│  │  Context Recall/Precision → CSV + JSON                   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Stack

- **Frontend**: Next.js, Tailwind CSS, shadcn/ui, assistant-ui
- **Backend**: FastAPI, LlamaIndex
- **Embeddings**: BAAI/bge-small-en-v1.5
- **Vector DB**: FAISS
- **LLM**: Ollama + Llama 3.2 (local)
- **Evaluation**: RAGAS

## Corpus

10 Markdown documents covering:
- Python decorators, async/await
- SQL JOINs, PostgreSQL indexing
- Docker Compose, Git rebase
- Linux permissions, REST API design
- CI/CD pipelines, Web security

## Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- Ollama (with `llama3.2` model)

### Backend

```bash
cd backend
python3 -m venv .venv

Install Python deps + pull Ollama model:

```bash
pip install llama-index llama-index-embeddings-huggingface llama-index-llms-ollama llama-index-vector-stores-faiss faiss-cpu sentence-transformers fastapi uvicorn pandas ragas datasets
ollama pull llama3.2
```

Build the index and start the API:

```bash
PYTHONPATH=. python -m app.ingestion
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npx shadcn@latest add button card input scroll-area separator table -y
npm run dev
```

Open http://localhost:3000

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Backend status |
| `/query` | POST | Ask a question |

```json
POST /query
{"query": "What is a LEFT JOIN in SQL?"}

Response:
{
  "answer": "A LEFT JOIN returns all rows from the left table...",
  "citations": [
    {"score": 0.83, "text": "...", "source": "sql-joins.md"},
    {"score": 0.78, "text": "...", "source": "sql-joins.md"}
  ]
}
```

## Evaluation

Run RAGAS evaluation across 3 configurations:

```bash
PYTHONPATH=. python evaluation/run_experiments.py
```

### Experiment Configs

| Config | Chunk Size | Overlap | Top-K |
|--------|-----------|---------|-------|
| A (baseline) | 512 | 128 | 3 |
| B (large chunks) | 1024 | 256 | 5 |
| C (more docs) | 512 | 128 | 5 |

### Metrics

| Config | Faithfulness | Relevancy | Recall | Precision | Latency (s) |
|--------|-------------|-----------|--------|-----------|-------------|
| A | — | — | — | — | — |
| B | — | — | — | — | — |
| C | — | — | — | — | — |

*Run experiments to populate metrics.*

## Project Structure

```
DomainRAG/
├── backend/
│   ├── app/
│   │   ├── config.py          # Settings
│   │   ├── ingestion.py        # Load, chunk, embed, index
│   │   ├── query_engine.py     # Retrieve + generate
│   │   ├── evaluation.py       # RAGAS pipeline
│   │   ├── models.py           # Pydantic schemas
│   │   └── main.py             # FastAPI server
│   ├── data/
│   │   └── raw/                # 10 corpus documents
│   ├── evaluation/
│   │   ├── test_set.csv        # 15 Q&A pairs
│   │   ├── run_experiments.py  # Multi-config experiments
│   │   └── results/            # Metrics output
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   │   ├── chat-interface.tsx
│   │   │   ├── citation-card.tsx
│   │   │   └── results-table.tsx
│   │   └── lib/
│   │       └── api.ts
│   └── package.json
└── README.md
```

## Resume

Built a domain-specific retrieval-augmented QA system using Next.js, Tailwind, shadcn/ui, LlamaIndex, BAAI/bge embeddings, FAISS vector store, Ollama LLM, and RAGAS evaluation to compare retrieval strategies and improve grounded answer quality.