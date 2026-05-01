import grpc
import grpc.aio

from ai_agent_service.core.config import get_settings
from ai_agent_service.services import session_store
from ai_agent_service.services.chat_service import answer_query
from ai_agent_service.services.llm.factory import get_llm
from shared.app_core.logging import get_logger
from shared.grpc_gen import agentic_pb2, agentic_pb2_grpc

logger = get_logger("agentic-service")


class AgenticServicer(agentic_pb2_grpc.AgenticServiceServicer):
    def __init__(self) -> None:
        self._settings = get_settings()
        self._llm = get_llm(self._settings)

    async def Chat(self, request: agentic_pb2.ChatRequest, context: grpc.aio.ServicerContext):
        sid = request.session_id or session_store.new_session_id()
        top_k = request.top_k if request.top_k > 0 else 3

        logger.info("grpc_chat", session_id=sid, query_len=len(request.query))
        try:
            answer, sources, confidence = await answer_query(
                query=request.query,
                top_k=top_k,
                session_id=sid,
                llm=self._llm,
                settings=self._settings,
            )
            return agentic_pb2.ChatResponse(
                answer=answer,
                sources=sources,
                confidence=confidence,
                session_id=sid,
            )
        except Exception as exc:
            logger.error("chat_error", error=str(exc))
            await context.abort(grpc.StatusCode.INTERNAL, "Chat processing failed")
