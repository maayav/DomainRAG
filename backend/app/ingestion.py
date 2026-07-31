"""Ingestion pipeline: load, chunk, embed, and index documents."""
import os
import logging

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore
import faiss

from app import config as cfg
from app.config import DATA_DIR, FAISS_DIR, EMBED_MODEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _embedding_dimension(embed_model) -> int:
    """Derive the embedding dimension from the model, not a hardcoded value."""
    st_model = embed_model._model
    for attr in ("get_sentence_embedding_dimension", "get_embedding_dimension"):
        getter = getattr(st_model, attr, None)
        if getter is not None:
            return int(getter())
    return len(embed_model.get_text_embedding("probe"))


def build_index(chunk_size: int | None = None, chunk_overlap: int | None = None):
    chunk_size = chunk_size if chunk_size is not None else cfg.CHUNK_SIZE
    chunk_overlap = chunk_overlap if chunk_overlap is not None else cfg.CHUNK_OVERLAP

    os.makedirs(FAISS_DIR, exist_ok=True)

    embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL)
    Settings.embed_model = embed_model
    splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    Settings.node_parser = splitter
    Settings.transformations = [splitter]

    logger.info(f"Loading documents from {DATA_DIR}")
    documents = SimpleDirectoryReader(DATA_DIR).load_data()
    logger.info(f"Loaded {len(documents)} documents")

    logger.info("Creating FAISS index")
    dimension = _embedding_dimension(embed_model)
    logger.info(f"Embedding dimension: {dimension}")
    faiss_index = faiss.IndexFlatL2(dimension)
    vector_store = FaissVectorStore(faiss_index=faiss_index)

    logger.info(f"Building vector store index (chunk_size={chunk_size}, overlap={chunk_overlap})")
    index = VectorStoreIndex.from_documents(
        documents,
        vector_store=vector_store,
        show_progress=True,
    )

    index.storage_context.persist(persist_dir=FAISS_DIR)
    faiss.write_index(faiss_index, os.path.join(FAISS_DIR, "index.faiss"))
    logger.info(f"Index persisted to {FAISS_DIR}")
    return index


def load_index():
    from llama_index.core import StorageContext, load_index_from_storage, Settings as LoadSettings
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    LoadSettings.embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL)

    faiss_path = os.path.join(FAISS_DIR, "index.faiss")
    if not os.path.exists(faiss_path):
        raise FileNotFoundError(f"FAISS index not found at {faiss_path}. Run ingestion first.")

    faiss_index = faiss.read_index(faiss_path)
    vector_store = FaissVectorStore(faiss_index=faiss_index)
    storage_context = StorageContext.from_defaults(persist_dir=FAISS_DIR)
    index = load_index_from_storage(storage_context, vector_store=vector_store)
    return index


if __name__ == "__main__":
    build_index()