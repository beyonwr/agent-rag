import logging
import uuid
from collections import defaultdict

from fastapi import FastAPI, Request 
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService 
from google.adk.runners import Runner 
from google.adk.sessions.database_session_service import DatabaseSessionService 
from google.genai import types

from .agent import root_agent
from .constants.constants import APP_NAME, SESSION_DB_URL

logger = logging.getLogger(__name__)

# --- Session service & Runner ---
session_service = DatabaseSessionService(db_url=SESSION_DB_URL)
artifact_service = InMemoryArtifactService()
runner = Runner(
    app_name=APP_NAME,
    agent=root_agent,
    session_service=session_service,
    artifact_service=artifact_service,
)

# --- IP -> session_id mapping (in-memory) ---
_ip_session_map: dict[str, str] = defaultdict(str)

app = FastAPI(title="RAG Agent Service")


# --- Request/Response models ---
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    response: str


class SessionInfo(BaseModel):
    session_id: str
    user_id: str


# --- Helpers ---
def _get_user_id(request: Request) -> str:

    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"
    # Sanitize IP for use as user_id
    return ip.replace(".", "_").replace(":", "_")


async def _get_or_create_session(user_id: str, session_id: str | None = None):

    if session_id:
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )
        if session:
            return session

    # Create new session
    new_session = await session_service.create_session(
        app_name=APP_NAME, user_id=user_id
    )
    return new_session


# --- Endpoints ---
@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest):

    user_id = _get_user_id(request)

    # Determine session_id
    session_id = body.session_id
    if not session_id:
        session_id = _ip_session_map.get(user_id)

    session = await _get_or_create_session(user_id, session_id)
    _ip_session_map[user_id] = session.id 

    # Build user message
    user_content = types.Content(
        parts=[types.Part(text=body.message)],
        role="user",
    )

    # Run agent
    final_response = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_content,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    final_response += part.text

    return ChatResponse(session_id=session_id, response=final_response)


@app.post("/session/new", response_model=SessionInfo)
async def new_session(request: Request): 

    user_id = _get_user_id(request)
    session = await session_service.create_session(
        app_name=APP_NAME, user_id=user_id
    )
    _ip_session_map[user_id] = session.id
    return SessionInfo(session_id=session.id, user_id=user_id)


@app.get("/sessions")
async def list_sessions(request: Request):

    user_id = _get_user_id(request)
    sessions_response = await session_service.list_sessions(
        app_name=APP_NAME, user_id=user_id
    )
    sessions = sessions_response.sessions if sessions_response else []
    return {
        "user_id": user_id,
        "sessions": [
            {"session_id": s.id, "user_id": s.user_id} for s in sessions
        ],
    }


@app.get("/health")
async def health():

    return {"status": "ok", "app_name": APP_NAME}
