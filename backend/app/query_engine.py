"""Query engine: retrieve context and generate answers with citations."""
import time
import logging

from llama_index.core import Settings

from app import config as cfg
from app import model_registry

logger = logging.getLogger(__name__)

SOURCE_URLS = {
    "python-decorators.md": "https://docs.python.org/3/glossary.html#term-decorator",
    "async-python.md": "https://docs.python.org/3/library/asyncio.html",
    "docker-compose.md": "https://docs.docker.com/compose/",
    "git-rebase.md": "https://git-scm.com/docs/git-rebase",
    "linux-permissions.md": "https://www.gnu.org/software/coreutils/manual/html_node/File-permissions.html",
    "postgres-indexing.md": "https://www.postgresql.org/docs/current/indexes.html",
    "rest-api-design.md": "https://restfulapi.net/",
    "sql-joins.md": "https://www.postgresql.org/docs/current/queries-table-expressions.html",
    "web-security.md": "https://owasp.org/www-project-top-ten/",
    "ci-cd-basics.md": "https://docs.github.com/en/actions",
    "architecture-scaling.md": "https://learn.microsoft.com/en-us/azure/architecture/guide/",
    "traffic-reliability.md": "https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker",
    "production-security.md": "https://owasp.org/www-project-web-security-testing-guide/",
    "production-checklist.md": "https://learn.microsoft.com/en-us/azure/well-architected/",
}


class CircuitBreaker:
    def __init__(self, threshold: int = 3, reset_timeout: int = 60):
        self.threshold = threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "closed"

    def reset(self):
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "closed"

    def call(self, func, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = "half-open"
            else:
                raise RuntimeError("Circuit breaker is open. LLM service unavailable.")
        try:
            result = func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.threshold:
                self.state = "open"
            raise e


_circuit_breaker = CircuitBreaker(
    threshold=cfg.CIRCUIT_BREAKER_THRESHOLD,
    reset_timeout=cfg.CIRCUIT_BREAKER_RESET,
)


def _wrap_ollama():
    return model_registry.make_llm()


def create_query_engine(index, top_k: int | None = None):
    Settings.llm = _wrap_ollama()
    top_k = top_k if top_k is not None else cfg.TOP_K
    query_engine = index.as_query_engine(
        similarity_top_k=top_k,
        response_mode="compact",
    )
    return query_engine


def _retrieve_filtered(index, question: str, top_k: int | None = None):
    """Retrieve with a recall cushion, then drop chunks below the similarity floor.

    Retrieves `top_k * 2` candidates so filtering still leaves up to `top_k`
    genuinely relevant chunks. Returns (context_text, citations).
    """
    top_k = top_k if top_k is not None else cfg.TOP_K
    retriever = index.as_retriever(similarity_top_k=top_k * 2)
    nodes = [
        node for node in retriever.retrieve(question)
        if node.score >= cfg.MIN_SIMILARITY
    ][:top_k]

    citations = []
    context_text = ""
    for node in nodes:
        source_name = node.node.metadata.get("file_name", "unknown")
        chunk = node.node.get_content()
        citations.append({
            "score": float(node.score),
            "text": chunk[:300],
            "source": source_name,
            "url": node.node.metadata.get("source_url") or SOURCE_URLS.get(source_name, ""),
        })
        context_text += f"\n---\nSource: {source_name}\n{chunk}\n"

    return context_text, citations


NO_MATCH_ANSWER = (
    "I could not find anything relevant in the knowledge base for that question. "
    "The closest chunks score below the retrieval confidence threshold, so nothing "
    "was used as context. You could ask about the topics already in the corpus, or "
    "add a document and ask again."
)


def _complete_with_fallback(prompt: str) -> str:
    """Generate an answer, auto-falling back to the local model once if the
    active provider fails (e.g. dead API key, retired model slug, rate limit)."""
    try:
        return _circuit_breaker.call(lambda: _wrap_ollama().complete(prompt))
    except Exception as e:
        if model_registry.enable_fallback(str(e)):
            logger.error(f"Provider failed ({e}); retrying on local {model_registry.get_config()['model']}")
            _circuit_breaker.reset()
            return _circuit_breaker.call(lambda: _wrap_ollama().complete(prompt))
        raise


def query_index(index, question: str, top_k: int | None = None, query_engine=None):
    context_text, citations = _retrieve_filtered(index, question, top_k=top_k)
    if not citations:
        return {"answer": NO_MATCH_ANSWER, "citations": []}

    prompt = f"""{cfg.SYSTEM_PROMPT}

Context:
{context_text}

Question: {question}

Answer:"""

    answer = _complete_with_fallback(prompt)
    return {
        "answer": str(answer),
        "citations": citations,
    }


def retrieve_context(index, question: str, top_k: int | None = None):
    return _retrieve_filtered(index, question, top_k=top_k)