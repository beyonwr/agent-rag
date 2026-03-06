import os

# Retrieval settings
TOP_K_RETRIEVAL = int(os.getenv("RAG_TOP_K", "5"))
ENSEMBLE_WEIGHTS = [0.5, 0.5]

# Paths
_PROJECT_ROOT = os.getenv("RAG_PROJECT_ROOT", "./")

DOCUMENT_JSON_PATH = os.getenv(
    "RAG_DOCUMENT_JSON_PATH",
    "/secret_data/xxxxx/10doc_data/10Doc_Test.json",
)
VECTOR_DB_PATH = os.getenv(
    "RAG_VECTOR_DB_PATH",
    "/secret_data/xxxxx/10doc_data/10Doc_Test_Pathmodified",
)
EMBEDDING_MODEL_PATH = os.getenv(
    "RAG_EMBEDDING_MODEL_PATH",
    os.path.join(_PROJECT_ROOT, "Models", "huggingface", "dragnokue-BGE-m3-ko"),
)

# Image path conversion
IMAGE_PATH_OLD_PREFIX = os.getenv("RAG_IMAGE_OLD_PREFIX", "/home/report/")
IMAGE_PATH_NEW_PREFIX = os.getenv("RAG_IMAGE_NEW_PREFIX", "/secret_data/report")
