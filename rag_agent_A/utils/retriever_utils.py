import json
import logging
import os
import re

os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

from konlpy.tag import Okt
from langchain_classic.retrievers import EnsembleRetriever
from langchain_classic.schema import Document 
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from ..constants.constants import (
    DOCUMENT_JSON_PATH,
    EMBEDDING_MODEL_PATH,
    ENSEMBLE_WEIGHTS,
    IMAGE_PATH_NEW_PREFIX,
    IMAGE_PATH_OLD_PREFIX,
    TOP_K_RETRIEVAL,
    VECTOR_DB_PATH,
)

logger = logging.getLogger(__name__)

# --- Korean morpheme analyzer (singleton) ---
okt = Okt()


def preprocess_func_okt(text: str) -> list[str]:
    return [token for token, _ in okt.pos(text)]


# --- Load documents ---
logger.info("Loading documents from %s", DOCUMENT_JSON_PATH)
with open(DOCUMENT_JSON_PATH, "r", encoding="utf-8") as f:
    loaded_docs_json = json.load(f)
loaded_docs = [Document(**doc) for doc in loaded_docs_json]
logger.info("Loaded %d documents", len(loaded_docs))

# --- Sparse retriever (BM25) ---
sparse_retriever = BM25Retriever.from_documents(
    documents=loaded_docs, preprocess_func=preprocess_func_okt
)
sparse_retriever.k = TOP_K_RETRIEVAL
logger.info("Sparse (BM25) retriever initialized")

# --- Dense retriever (FAISS) ---
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_PATH)
vectorstore = FAISS.load_local(
    VECTOR_DB_PATH, embeddings=embeddings, allow_dangerous_deserialization=True
)
dense_retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K_RETRIEVAL})
logger.info("Dense (FAISS) retriever initialized")

# --- Ensemble retriever ---
ensemble_retriever = EnsembleRetriever(
    retrievers=[sparse_retriever, dense_retriever],
    weights=ENSEMBLE_WEIGHTS,
    search_kwargs={"k": TOP_K_RETRIEVAL},
)
logger.info("Ensemble retriever initialized (weights=%s, k=%d)", ENSEMBLE_WEIGHTS, TOP_K_RETRIEVAL)


def fix_image_paths(text: str) -> str:
    """Replace old image/table paths with the new serving prefix."""
    return text.replace(IMAGE_PATH_OLD_PREFIX, IMAGE_PATH_NEW_PREFIX)


def retrieve_documents(query: str) -> list[dict]:

    docs = ensemble_retriever.invoke(query)
    results = []
    for doc in docs:
        content = fix_image_paths(doc.page_content)
        metadata = doc.metadata.copy()
        # Fix image paths in metadata values
        for key, val in metadata.items():
            if isinstance(val, str):
                metadata[key] = fix_image_paths(val)
            elif isinstance(val, list):
                metadata[key] = [
                    fix_image_paths(item) if isinstance(item, str) else item
                    for item in val
                ]
        results.append(
            {
                "content": content,
                "metadata": metadata,
                "source": metadata.get("source", ""),
                "page": metadata.get("page", ""),
            }
        )
    logger.debug("Retrieved %d documents for query: %s", len(results), query[:80])
    return results
    