import logging
import os

from fastapi import FastAPI
from pydantic import BaseModel

from .retriever import retrieve_documents

logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Search API")


class SearchRequest(BaseModel):
    query: str
    top_k: int | None = None


@app.post("/search")
async def search(body: SearchRequest):
    try:
        results = retrieve_documents(body.query, top_k=body.top_k)
        return {
            "status": "success",
            "query": body.query,
            "total": len(results),
            "results": results,
        }
    except Exception as e:
        logger.exception("Search failed for query: %s", body.query)
        return {
            "status": "error",
            "message": str(e),
            "results": [],
        }


@app.get("/health")
async def health():
    return {"status": "ok"}
