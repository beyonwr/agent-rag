import logging
import mimetypes
import os

from google.adk.tools import ToolContext 
from google.genai import types

from ..constants.constants import RAG_LAST_SEARCH_QUERY, RAG_LAST_SEARCH_RESULTS
from ..utils.retriever_utils import retrieve_documents

logger = logging.getLogger(__name__)


async def _save_image_artifacts(
    tool_context: ToolContext, results: list[dict]
) -> list[str]:

    saved = []
    seen = set()

    for result in results:
        for img_path in result.get("metadata", {}).get("image", []):
            if img_path in seen or not os.path.isfile(img_path):
                continue
            seen.add(img_path)

            with open(img_path, "rb") as f:
                data = f.read()

            mime_type = mimetypes.guess_type(img_path)[0] or "image/png"
            artifact = types.Part(
                inline_data=types.Blob(mime_type=mime_type, data=data)
            )

            # 고유 파일명: 보고서ID_이미지명.png
            report_id = os.path.basename(
                os.path.dirname(os.path.dirname(img_path))
            )
            filename = f"{report_id}_{os.path.basename(img_path)}"

            await tool_context.save_artifact(filename=filename, artifact=artifact)
            saved.append(filename)

    return saved


async def search_tech_reports(query: str, tool_context: ToolContext) -> dict:

    try:
        results = retrieve_documents(query)

        # Save to session state for multi-turn context
        tool_context.state[RAG_LAST_SEARCH_QUERY] = query
        tool_context.state[RAG_LAST_SEARCH_RESULTS] = results

        if not results:
            return {
                "status": "success",
                "message": f"'{query}'에 대한 검색 결과가 없습니다.",
                "data": [],
                "saved_artifacts": [],
            }

        saved_artifacts = await _save_image_artifacts(tool_context, results)

        return {
            "status": "success",
            "message": f"'{query}'에 대해 {len(results)}건의 문서를 검색했습니다.",
            "data": results,
            "saved_artifacts": saved_artifacts,
        }
    except Exception as e:
        logger.exception("Error in search_tech_reports for query: %s", query)
        return {
            "status": "error",
            "message": f"검색 중 오류가 발생했습니다. {e}",
            "data": [],
        }
