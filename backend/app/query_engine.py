"""Query engine: retrieve context and generate answers with citations."""
import time
import logging

from llama_index.core import Settings
from llama_index.llms.ollama import Ollama

from app.config import LLM_MODEL, LLM_TEMPERATURE, LLM_TIMEOUT, TOP_K, CIRCUIT_BREAKER_THRESHOLD, CIRCUIT_BREAKER_RESET

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


_circuit_breaker = CircuitBreaker(threshold=CIRCUIT_BREAKER_THRESHOLD, reset_timeout=CIRCUIT_BREAKER_RESET)


def _wrap_ollama():
    return Ollama(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        request_timeout=LLM_TIMEOUT,
    )


def create_query_engine(index):
    Settings.llm = _wrap_ollama()
    query_engine = index.as_query_engine(
        similarity_top_k=TOP_K,
        response_mode="compact",
    )
    return query_engine


def query_index(index, question: str):
    engine = create_query_engine(index)
    response = _circuit_breaker.call(engine.query, question)

    citations = []
    for node in response.source_nodes:
        source_name = node.node.metadata.get("file_name", "unknown")
        citations.append({
            "score": float(node.score),
            "text": node.node.get_content()[:300],
            "source": source_name,
            "url": SOURCE_URLS.get(source_name, ""),
        })

    return {
        "answer": str(response),
        "citations": citations,
    }


def retrieve_context(index, question: str):
    Settings.embed_model = index._embed_model
    retriever = index.as_retriever(similarity_top_k=TOP_K)
    nodes = retriever.retrieve(question)

    citations = []
    context_text = ""
    for node in nodes:
        source_name = node.node.metadata.get("file_name", "unknown")
        chunk = node.node.get_content()
        citations.append({
            "score": float(node.score),
            "text": chunk[:300],
            "source": source_name,
            "url": SOURCE_URLS.get(source_name, ""),
        })
        context_text += f"\n---\nSource: {source_name}\n{chunk}\n"

    return context_text, citations