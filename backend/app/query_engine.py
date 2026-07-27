"""Query engine: retrieve context and generate answers with citations."""
import logging

from llama_index.core import Settings
from llama_index.llms.ollama import Ollama

from app.config import LLM_MODEL, LLM_TEMPERATURE, LLM_TIMEOUT, TOP_K

logger = logging.getLogger(__name__)


def create_query_engine(index):
    Settings.llm = Ollama(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        request_timeout=LLM_TIMEOUT,
    )

    query_engine = index.as_query_engine(
        similarity_top_k=TOP_K,
        response_mode="compact",
    )

    return query_engine


def query_index(index, question: str):
    engine = create_query_engine(index)
    response = engine.query(question)

    citations = []
    for node in response.source_nodes:
        citations.append({
            "score": float(node.score),
            "text": node.node.get_content()[:300],
            "source": node.node.metadata.get("file_name", "unknown"),
        })

    return {
        "answer": str(response),
        "citations": citations,
    }