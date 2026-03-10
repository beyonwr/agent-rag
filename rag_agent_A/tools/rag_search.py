import base64
import logging
import re

import httpx
from google.adk.tools import ToolContext
from google.genai import types

from ..constants.constants import (
    RAG_API_BASE_URL,
    RAG_API_USER,
    RAG_LAST_SEARCH_QUERY,
    RAG_LAST_SEARCH_RESULTS,
)

logger = logging.getLogger(__name__)


async def _call_rag_api(query: str) -> dict:
    """Call the external RAG API /retrieve/techreport endpoint."""
    payload: dict = {"query": query, "user": RAG_API_USER}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{RAG_API_BASE_URL}/retrieve/techreport", json=payload
        )
        resp.raise_for_status()
        return resp.json()


async def _save_image_artifacts(
    tool_context: ToolContext, results: list[dict]
) -> list[str]:

    saved = []
    seen = set()

    for result in results:
        metadata = result.get("metadata", {})
        title = metadata.get("title", "unknown")
        # 파일명에 사용할 수 없는 문자 제거
        safe_title = re.sub(r'[^\w\-.]', '_', title)

        for idx, b64_str in enumerate(metadata.get("image", [])):
            key = f"{title}_{idx}"
            if key in seen:
                continue
            seen.add(key)

            data = base64.b64decode(b64_str)
            artifact = types.Part(
                inline_data=types.Blob(mime_type="image/png", data=data)
            )

            filename = f"{safe_title}_{idx}.png"
            await tool_context.save_artifact(filename=filename, artifact=artifact)
            saved.append(filename)

    return saved


async def search_tech_reports(query: str, tool_context: ToolContext) -> dict:

    try:
        api_response = await _call_rag_api(query)

        if api_response.get("status") == "error":
            return {
                "status": "error",
                "outputs": {
                    "message": "RAG API 오류",
                    "data": [],
                },
            }

        results = api_response.get("outputs", [])

        # Save to session state for multi-turn context
        tool_context.state[RAG_LAST_SEARCH_QUERY] = query
        tool_context.state[RAG_LAST_SEARCH_RESULTS] = results

        if not results:
            return {
                "status": "success",
                "outputs": {
                    "message": f"'{query}'에 대한 검색 결과가 없습니다.",
                    "data": [],
                    "saved_artifacts": [],
                },
            }

        saved_artifacts = await _save_image_artifacts(tool_context, results)

        return {
            "status": "success",
            "outputs": {
                "message": f"'{query}'에 대해 {len(results)}건의 문서를 검색했습니다.",
                "data": results,
                "saved_artifacts": saved_artifacts,
            },
        }
    except httpx.HTTPStatusError as e:
        logger.exception("RAG API HTTP error for query: %s", query)
        return {
            "status": "error",
            "outputs": {
                "message": f"RAG API 호출 실패 (HTTP {e.response.status_code})",
                "data": [],
            },
        }
    except Exception as e:
        logger.exception("Error in search_tech_reports for query: %s", query)
        return {
            "status": "error",
            "outputs": {
                "message": f"검색 중 오류가 발생했습니다. {e}",
                "data": [],
            },
        }
