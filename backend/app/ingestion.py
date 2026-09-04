"""Ingestion pipeline: load, chunk, embed, and index documents."""
import os
import re
import logging

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore
import faiss

from app.config import (
    DATA_DIR, UPLOADS_DIR, SCRAPED_DIR, FAISS_DIR,
    CHUNK_SIZE, CHUNK_OVERLAP, EMBED_MODEL,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_embed_model():
    return HuggingFaceEmbedding(model_name=EMBED_MODEL)


def embedding_dimension(embed_model) -> int:
    """Derive the embedding dimension from the model instead of hardcoding it."""
    return len(embed_model.get_query_embedding("dimension probe"))


def _source_url_metadata(path: str) -> dict:
    """Attach a source_url to scraped/uploaded files that declare one in front matter."""
    meta: dict = {"file_name": os.path.basename(path)}
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            head = f.read(2048)
        match = re.search(r"^source_url:\s*(\S+)\s*$", head, re.MULTILINE | re.IGNORECASE)
        if match:
            meta["source_url"] = match.group(1)
    except OSError:
        pass
    return meta


def _load_directory(directory: str):
    if not os.path.isdir(directory) or not any(os.scandir(directory)):
        return []
    return SimpleDirectoryReader(directory, file_metadata=_source_url_metadata).load_data()


def load_documents(include_uploads: bool = True):
    documents = _load_directory(DATA_DIR)
    if include_uploads:
        documents += _load_directory(UPLOADS_DIR)
        documents += _load_directory(SCRAPED_DIR)
    return documents


def build_index(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP,
                persist_dir=FAISS_DIR, include_uploads: bool = True):
    if persist_dir != FAISS_DIR:
        os.makedirs(persist_dir, exist_ok=True)

    embed_model = create_embed_model()
    Settings.embed_model = embed_model
    # Set node_parser AND transformations explicitly: llama-index lazily caches
    # Settings.transformations on first access, so a stale default parser can
    # otherwise survive into later rebuilds (server process) and skip chunking.
    splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    Settings.node_parser = splitter
    Settings.transformations = [splitter]

    documents = load_documents(include_uploads=include_uploads)
    if not documents:
        raise FileNotFoundError(f"No documents found. Add files to {DATA_DIR}; uploads and scraped sources "
                                f"are included automatically.")
    logger.info(f"Loaded {len(documents)} document(s)")

    dimension = embedding_dimension(embed_model)
    logger.info(f"Creating FAISS index (dimension={dimension})")
    faiss_index = faiss.IndexFlatL2(dimension)
    vector_store = FaissVectorStore(faiss_index=faiss_index)

    logger.info("Building vector store index")
    index = VectorStoreIndex.from_documents(
        documents,
        vector_store=vector_store,
        show_progress=True,
    )

    index.storage_context.persist(persist_dir=persist_dir)
    faiss.write_index(faiss_index, os.path.join(persist_dir, "index.faiss"))
    logger.info(f"Index persisted to {persist_dir}")
    return index


def load_index(persist_dir=FAISS_DIR):
    from llama_index.core import StorageContext, load_index_from_storage, Settings as LoadSettings

    LoadSettings.embed_model = create_embed_model()

    faiss_path = os.path.join(persist_dir, "index.faiss")
    if not os.path.exists(faiss_path):
        raise FileNotFoundError(f"FAISS index not found at {faiss_path}. Run ingestion first.")

    faiss_index = faiss.read_index(faiss_path)
    vector_store = FaissVectorStore(faiss_index=faiss_index)
    storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
    index = load_index_from_storage(storage_context, vector_store=vector_store)
    return index


if __name__ == "__main__":
    build_index()