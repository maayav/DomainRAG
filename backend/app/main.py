"""FastAPI application for the RAG system."""
import os
import json
import time
import logging
from contextlib import asynccontextmanager
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from llama_index.llms.ollama import Ollama

from app.config import (
    DATA_DIR, LLM_MODEL, LLM_TEMPERATURE, LLM_TIMEOUT, SYSTEM_PROMPT,
    RATE_LIMIT_WINDOW, RATE_LIMIT_MAX,
)
from app.models import QueryRequest, QueryResponse, Citation
from app.ingestion import build_index, load_index
from app.query_engine import query_index, retrieve_context, create_query_engine
from app.auth import AuthMiddleware, API_KEY
from app.logger import StructuredLogger

logger = StructuredLogger(__name__)

index = None
query_engine = None

# Rate limiting state
_rate_store: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(ip: str) -> bool:
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    timestamps = [t for t in _rate_store[ip] if t > window_start]
    _rate_store[ip] = timestamps
    if len(timestamps) >= RATE_LIMIT_MAX:
        return False
    _rate_store[ip].append(now)
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    global index, query_engine
    try:
        index = load_index()
        logger.info("Loaded existing index")
    except Exception:
        logger.info("Building new index")
        index = build_index()
    query_engine = create_query_engine(index)
    yield


app = FastAPI(title="DomainRAG", lifespan=lifespan)

# Auth is header-based (x-api-key), so credentials are not needed; origins
# are configurable via CORS_ORIGINS (comma-separated), defaulting to any origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", extra={
        "path": request.url.path,
        "method": request.method,
        "client_ip": request.client.host if request.client else None,
    })
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path not in ("/health", "/docs", "/openapi.json", "/redoc"):
        ip = request.client.host if request.client else "unknown"
        if not _check_rate_limit(ip):
            logger.warning("Rate limit exceeded", extra={"client_ip": ip})
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Try again later."},
            )
    return await call_next(request)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed = time.time() - start
    user_id = request.headers.get("x-api-key", "")[:8] if API_KEY else "anonymous"
    logger.info("Request completed", extra={
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "elapsed_ms": round(elapsed * 1000),
        "user_id": user_id + "..." if len(user_id) > 8 else user_id,
    })
    return response


@app.get("/health")
async def health():
    doc_count = len(index.docstore.docs) if index else 0
    return {"status": "ok", "documents": doc_count}


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    result = query_index(index, request.query, query_engine=query_engine)
    return QueryResponse(
        answer=result["answer"],
        citations=[Citation(**c) for c in result["citations"]],
    )


@app.post("/query/stream")
async def query_stream(request: QueryRequest):
    """SSE streaming endpoint: emits thinking steps, citations, then answer tokens."""

    async def event_generator():
        yield sse_event("thinking", {"step": "Understanding your question..."})

        yield sse_event("thinking", {"step": "Searching knowledge base..."})
        try:
            context_text, citations = retrieve_context(index, request.query)
        except Exception:
            logger.error("Context retrieval failed", extra={"query": request.query[:100]})
            yield sse_event("error", {"detail": "Failed to retrieve context"})
            return

        yield sse_event("thinking", {"step": f"Found {len(citations)} relevant sources"})
        yield sse_event("citations", citations)

        yield sse_event("thinking", {"step": "Generating answer..."})

        prompt = f"""{SYSTEM_PROMPT}

Context:
{context_text}

Question: {request.query}

Answer:"""

        llm = Ollama(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            request_timeout=LLM_TIMEOUT,
        )

        full_response = ""
        try:
            for token in llm.stream_complete(prompt):
                chunk = token.delta
                if chunk:
                    full_response += chunk
                    yield sse_event("token", {"text": chunk})
        except Exception:
            logger.error("LLM streaming failed", extra={"query": request.query[:100]})
            yield sse_event("error", {"detail": "Answer generation failed"})
            return

        yield sse_event("done", {"answer": full_response})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def sse_event(event_type: str, data) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"