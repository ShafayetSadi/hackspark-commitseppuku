from ai_agent_service.core.config import AIAgentSettings
from ai_agent_service.services import session_store
from ai_agent_service.services.llm.base import BaseLLM
from ai_agent_service.services.rag.context_builder import build_context
from ai_agent_service.services.rag.relevance import is_relevant_query
from ai_agent_service.services.rag.retriever import retrieve_documents


async def answer_query(
    query: str,
    top_k: int,
    session_id: str,
    llm: BaseLLM,
    settings: AIAgentSettings,
) -> tuple[str, list[str], float]:
    if not is_relevant_query(query, settings):
        answer = "The query is outside the supported platform and hackathon knowledge scope."
        await session_store.append_message(session_id, "user", query)
        await session_store.append_message(session_id, "assistant", answer)
        return answer, [], 0.0

    history = await session_store.load_history(session_id)
    documents = retrieve_documents(query, top_k)
    context = build_context(documents)

    answer, sources, confidence = await llm.generate_answer(query, documents, context, history)

    await session_store.append_message(session_id, "user", query)
    await session_store.append_message(session_id, "assistant", answer)

    return answer, sources, confidence
