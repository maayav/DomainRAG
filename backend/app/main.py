"""FastAPI application for the RAG system."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import DATA_DIR
from app.models import QueryRequest, QueryResponse, Citation
from app.ingestion import build_index, load_index
from app.query_engine import query_index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

index = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global index
    try:
        index = load_index()
        logger.info("Loaded existing index")
    except Exception:
        logger.info("Building new index")
        index = build_index()
    yield


app = FastAPI(title="DomainRAG", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "documents": len(index.documents) if index else 0}


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    result = query_index(index, request.query)
    return QueryResponse(
        answer=result["answer"],
        citations=[Citation(**c) for c in result["citations"]],
    )