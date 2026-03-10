import os

APP_NAME = "rag_agent"

# RAG API
RAG_API_BASE_URL = os.getenv("RAG_API_BASE_URL", "http://localhost:8080")
RAG_API_USER = os.getenv("RAG_API_USER", "default")

# Session DB
SESSION_DB_URL = "sqlite:///./rag_agent_session.db"

# State keys
RAG_LAST_SEARCH_QUERY = "rag_last_search_query"
RAG_LAST_SEARCH_RESULTS = "rag_last_search_results"
