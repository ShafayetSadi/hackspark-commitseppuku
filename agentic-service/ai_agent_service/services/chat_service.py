from __future__ import annotations

from dataclasses import asdict, dataclass

from ai_agent_service.core.config import AIAgentSettings
from ai_agent_service.services import session_store
from ai_agent_service.services.llm.base import BaseLLM
from ai_agent_service.services.tool_executor import describe_tools, execute_tool


@dataclass(frozen=True, slots=True)
class ChatResult:
    answer: str
    sources: list[str]
    confidence: float
    session_id: str


async def process_chat(
    *,
    query: str,
    session_id: str | None,
    llm: BaseLLM,
    settings: AIAgentSettings,
) -> ChatResult:
    sid = session_id or session_store.new_session_id()
    summary = await session_store.load_summary(sid)
    recent_messages = await session_store.load_recent_messages(sid, settings.chat_recent_messages_limit)
    meta = await session_store.load_meta(sid)

    if not meta:
        title = await llm.generate_session_title(query)
        await session_store.ensure_session_meta(sid, title, summary)

    tool_decision = await llm.decide_tool(summary, recent_messages, query, describe_tools())
    tool_payload: dict | None = None
    sources = ["session-memory"]
    confidence = 0.72

    if tool_decision.tool_name:
        try:
            execution = execute_tool(tool_decision.tool_name, tool_decision.arguments)
        except ValueError:
            execution = None
        if execution is not None:
            tool_payload = {
                "tool_name": execution.name,
                "arguments": execution.arguments,
                "result": execution.result,
            }
            sources = [f"tool:{execution.name}"]
            confidence = 0.9

    answer = await llm.generate_final_answer(summary, recent_messages, query, tool_payload)

    await session_store.append_message(sid, "user", query)
    await session_store.append_message(sid, "assistant", answer)

    updated_history = await session_store.load_recent_messages(sid, settings.summary_message_window)
    updated_summary = await llm.summarize_session(summary, updated_history)
    await session_store.update_summary(sid, updated_summary)
    await session_store.touch_meta(sid)

    return ChatResult(
        answer=answer,
        sources=sources,
        confidence=confidence,
        session_id=sid,
    )


async def list_chat_sessions() -> list[dict]:
    return await session_store.list_sessions()


async def get_chat_history(session_id: str) -> list[dict]:
    return await session_store.load_history(session_id)


async def delete_chat_session(session_id: str) -> bool:
    return await session_store.delete_session(session_id)


def to_response_payload(result: ChatResult) -> dict:
    return asdict(result)
