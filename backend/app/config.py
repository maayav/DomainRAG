"""Configuration settings for the RAG system."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
FAISS_DIR = os.path.join(BASE_DIR, "data", "faiss_index")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

CHUNK_SIZE = 512
CHUNK_OVERLAP = 128
TOP_K = 3

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
LLM_MODEL = "qwen3:8b"
LLM_TEMPERATURE = 0.1
LLM_TIMEOUT = 120

SYSTEM_PROMPT = """You are a technical assistant. Answer the question using only the provided context. If the context does not contain enough information, say so. Cite your sources by referencing the document filename."""

# Security
API_KEY = os.environ.get("DOMAINRAG_API_KEY", "")
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 30

# Circuit breaker
CIRCUIT_BREAKER_THRESHOLD = 3
CIRCUIT_BREAKER_RESET = 60

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT = "json"