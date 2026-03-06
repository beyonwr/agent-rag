import os

APP_NAME = "rag_agent"

# Retrieval settings
TOP_K_RETRIEVAL = 5
ENSEMBLE_WEIGHTS = [0.5, 0.5]

# Paths (resolved relative to project root)
# _PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_PROJECT_ROOT = "./"

# DOCUMENT_JSON_PATH = os.path.join(_PROJECT_ROOT, "vectorDB", "10Doc_Test.json")
DOCUMENT_JSON_PATH = "/secret_data/xxxxx/10doc_data/10Doc_Test.json"
VECTOR_DB_PATH = "/secret_data/xxxxx/10doc_data/10Doc_Test_Pathmodified"
# VECTOR_DB_PATH = os.path.join(_PROJECT_ROOT, "VectorDB", "10Doc_Test")
EMBEDDING_MODEL_PATH = os.path.join(
    _PROJECT_ROOT, "Models", "huggingface", "dragnokue-BGE-m3-ko"
)

# Image path conversion
IMAGE_PATH_OLD_PREFIX = "/home/report/"
IMAGE_PATH_NEW_PREFIX = "/secret_data/report"

# Session DB
SESSION_DB_URL = "sqlite:///./rag_agent_session.db"

# State keys
RAG_LAST_SEARCH_QUERY = "rag_last_search_query"
RAG_LAST_SEARCH_RESULTS = "rag_last_search_results"
