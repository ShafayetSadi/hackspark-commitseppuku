from ai_agent_service.core.config import AIAgentSettings
from ai_agent_service.schemas.chat import ChatRequest, ChatResponse
from ai_agent_service.services.llm.mock_llm import MockLLM
from ai_agent_service.services.rag.context_builder import build_context
from ai_agent_service.services.rag.relevance import is_relevant_query
from ai_agent_service.services.rag.retriever import retrieve_documents


def answer_query(payload: ChatRequest, settings: AIAgentSettings) -> ChatResponse:
    if not is_relevant_query(payload.query, settings):
        return ChatResponse(
            answer="The query is outside the supported platform and hackathon knowledge scope.",
            sources=[],
            confidence=0.0,
        )

    documents = retrieve_documents(payload.query, payload.top_k)
    context = build_context(documents)
    llm = MockLLM()
    return llm.generate_answer(payload.query, documents, context)
