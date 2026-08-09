"""Configuration settings for the RAG system."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
FAISS_DIR = os.path.join(BASE_DIR, "data", "faiss_index")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
UPLOADS_DIR = os.path.join(BASE_DIR, "data", "uploads")
SCRAPED_DIR = os.path.join(BASE_DIR, "data", "scraped")

CHUNK_SIZE = 512
CHUNK_OVERLAP = 128
TOP_K = 3

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
LLM_MODEL = os.environ.get("DOMAINRAG_LLM_MODEL", "qwen3:8b")
LLM_TEMPERATURE = 0.1
LLM_TIMEOUT = 120

SYSTEM_PROMPT = """You are a technical assistant. Answer the question ONLY from the provided context. Begin directly with the answer, no preamble.
Use whatever the context does say, even if it is partial, and be explicit about what it does not cover.
If the context is empty or entirely unrelated to the question, state that the knowledge base does not cover the question. Never guess or invent."""

# Security
API_KEY = os.environ.get("DOMAINRAG_API_KEY", "")
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 30

# CORS
CORS_ORIGINS = [o.strip() for o in os.environ.get("DOMAINRAG_CORS_ORIGINS", "*").split(",") if o.strip()]

# Ingestion limits
MAX_UPLOAD_SIZE = int(os.environ.get("DOMAINRAG_MAX_UPLOAD_SIZE", str(10 * 1024 * 1024)))
ALLOWED_EXTENSIONS = {
    ".md", ".txt", ".rst", ".pdf",
    ".html", ".htm", ".csv",
    ".json", ".yaml", ".yml",
    ".docx", ".pptx", ".xlsx",
}

# Retrieval confidence: chunks scoring below this similarity are treated as
# "no relevant information" instead of being fed to the model as context.
MIN_SIMILARITY = float(os.environ.get("DOMAINRAG_MIN_SIMILARITY", "0.62"))

# Scraper
SCRAPE_TIMEOUT = int(os.environ.get("DOMAINRAG_SCRAPE_TIMEOUT", "15"))
SCRAPE_MAX_PAGES = int(os.environ.get("DOMAINRAG_SCRAPE_MAX_PAGES", "10"))
SCRAPE_USER_AGENT = os.environ.get(
    "DOMAINRAG_SCRAPE_USER_AGENT",
    "DomainRAG-bot/1.0 (+knowledge base builder)",
)

# Circuit breaker
CIRCUIT_BREAKER_THRESHOLD = 3
CIRCUIT_BREAKER_RESET = 60

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT = "json"