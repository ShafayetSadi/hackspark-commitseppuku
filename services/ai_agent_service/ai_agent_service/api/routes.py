from ai_agent_service.core.config import AIAgentSettings, get_settings
from ai_agent_service.schemas.chat import ChatRequest, ChatResponse
from ai_agent_service.services.chat_service import answer_query
from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("/health")
async def healthcheck() -> dict:
    return {"status": "ok", "service": "ai-agent-service"}


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    settings: AIAgentSettings = Depends(get_settings),
) -> ChatResponse:
    return answer_query(payload, settings)
