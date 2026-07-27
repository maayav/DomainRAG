"""Ingestion pipeline: load, chunk, embed, and index documents."""
import os
import logging

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore
import faiss

from app.config import DATA_DIR, FAISS_DIR, CHUNK_SIZE, CHUNK_OVERLAP, EMBED_MODEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_index():
    os.makedirs(FAISS_DIR, exist_ok=True)

    Settings.embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL)
    Settings.node_parser = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    logger.info(f"Loading documents from {DATA_DIR}")
    documents = SimpleDirectoryReader(DATA_DIR).load_data()
    logger.info(f"Loaded {len(documents)} documents")

    logger.info("Creating FAISS index")
    dimension = 384
    faiss_index = faiss.IndexFlatL2(dimension)
    vector_store = FaissVectorStore(faiss_index=faiss_index)

    logger.info("Building vector store index")
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