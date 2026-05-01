from ai_agent_service.core.config import AIAgentSettings, get_settings
from ai_agent_service.schemas.chat import (
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    ChatSessionsResponse,
    DeleteSessionResponse,
)
from ai_agent_service.services.chat_service import (
    delete_chat_session,
    get_chat_history,
    list_chat_sessions,
    process_chat,
    to_response_payload,
)
from ai_agent_service.services.llm.factory import get_llm
from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("/status")
async def status() -> dict:
    return {"service": "agentic-service", "status": "OK"}


@router.get("/health")
async def healthcheck() -> dict:
    return {"status": "ok", "service": "agentic-service"}


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    settings: AIAgentSettings = Depends(get_settings),
) -> ChatResponse:
    result = await process_chat(
        query=payload.query,
        session_id=payload.session_id,
        llm=get_llm(settings),
        settings=settings,
    )
    return ChatResponse(**to_response_payload(result))


@router.get("/chat/sessions", response_model=ChatSessionsResponse)
async def chat_sessions() -> ChatSessionsResponse:
    sessions = await list_chat_sessions()
    return ChatSessionsResponse(sessions=sessions)


@router.get("/chat/{session_id}/history", response_model=ChatHistoryResponse)
async def chat_history(session_id: str) -> ChatHistoryResponse:
    history = await get_chat_history(session_id)
    return ChatHistoryResponse(session_id=session_id, messages=history)


@router.delete("/chat/{session_id}", response_model=DeleteSessionResponse)
async def delete_session(session_id: str) -> DeleteSessionResponse:
    deleted = await delete_chat_session(session_id)
    return DeleteSessionResponse(session_id=session_id, deleted=deleted)
