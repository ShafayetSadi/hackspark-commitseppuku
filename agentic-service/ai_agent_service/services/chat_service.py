from __future__ import annotations

import time
from dataclasses import asdict, dataclass

from ai_agent_service.core.config import AIAgentSettings
from ai_agent_service.services import session_store
from ai_agent_service.services.llm.base import BaseLLM
from ai_agent_service.services.tool_executor import describe_tools, execute_tool
from shared.app_core.logging import get_logger

logger = get_logger("agentic-service.chat")


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
    t_start = time.monotonic()
    sid = session_id or session_store.new_session_id()
    is_new_session = session_id is None

    logger.info(
        "chat_query_received",
        session_id=sid,
        new_session=is_new_session,
        query_len=len(query),
        query_preview=query[:120],
    )

    summary = await session_store.load_summary(sid)
    recent_messages = await session_store.load_recent_messages(sid, settings.chat_recent_messages_limit)
    meta = await session_store.load_meta(sid)

    logger.debug(
        "chat_session_loaded",
        session_id=sid,
        has_summary=bool(summary),
        recent_message_count=len(recent_messages),
        has_meta=bool(meta),
    )

    if not meta:
        title = await llm.generate_session_title(query)
        await session_store.ensure_session_meta(sid, title, summary)
        logger.info("chat_session_created", session_id=sid, title=title)

    t_tool = time.monotonic()
    tool_decision = await llm.decide_tool(summary, recent_messages, query, describe_tools())

    logger.info(
        "chat_tool_decision",
        session_id=sid,
        tool_selected=tool_decision.tool_name,
        tool_arguments=tool_decision.arguments,
        needs_clarification=bool(tool_decision.clarification),
        decision_ms=round((time.monotonic() - t_tool) * 1000),
    )

    # If the LLM knows which tool to call but is missing arguments, ask the user
    # conversationally rather than attempting a doomed tool call.
    if tool_decision.clarification:
        answer = tool_decision.clarification
        sources = ["clarification"]
        confidence = 0.85
        logger.info("chat_clarification_requested", session_id=sid, tool=tool_decision.tool_name)
        await session_store.append_message(sid, "user", query)
        await session_store.append_message(sid, "assistant", answer)
        updated_history = await session_store.load_recent_messages(sid, settings.summary_message_window)
        updated_summary = await llm.summarize_session(summary, updated_history)
        await session_store.update_summary(sid, updated_summary)
        await session_store.touch_meta(sid)
        logger.info("chat_turn_complete", session_id=sid, sources=sources, confidence=confidence, total_ms=round((time.monotonic() - t_start) * 1000))
        return ChatResult(answer=answer, sources=sources, confidence=confidence, session_id=sid)

    tool_payload: dict | None = None
    sources = ["session-memory"]
    confidence = 0.72

    if tool_decision.tool_name:
        t_exec = time.monotonic()
        try:
            execution = await execute_tool(tool_decision.tool_name, tool_decision.arguments, settings)
        except Exception as exc:
            logger.warning(
                "chat_tool_execution_failed",
                session_id=sid,
                tool=tool_decision.tool_name,
                error=str(exc),
            )
            execution = None

        if execution is not None:
            tool_payload = {
                "tool_name": execution.name,
                "arguments": execution.arguments,
                "result": execution.result,
                "status": "ok",
            }
            sources = [f"tool:{execution.name}"]
            confidence = 0.9
            logger.info(
                "chat_tool_executed",
                session_id=sid,
                tool=execution.name,
                arguments=execution.arguments,
                result_keys=list(execution.result.keys()),
                exec_ms=round((time.monotonic() - t_exec) * 1000),
            )
        else:
            tool_payload = {
                "tool_name": tool_decision.tool_name,
                "status": "failed",
                "note": "Tool execution failed — data is unavailable. Do not guess or invent any numbers.",
            }
            sources = [f"tool:{tool_decision.tool_name}"]
            logger.info(
                "chat_tool_skipped",
                session_id=sid,
                tool=tool_decision.tool_name,
                reason="execution returned None",
            )

    t_llm = time.monotonic()
    answer = await llm.generate_final_answer(summary, recent_messages, query, tool_payload)
    logger.info(
        "chat_answer_generated",
        session_id=sid,
        answer_len=len(answer),
        tool_grounded=tool_payload is not None,
        llm_ms=round((time.monotonic() - t_llm) * 1000),
    )

    await session_store.append_message(sid, "user", query)
    await session_store.append_message(sid, "assistant", answer)

    updated_history = await session_store.load_recent_messages(sid, settings.summary_message_window)
    updated_summary = await llm.summarize_session(summary, updated_history)
    await session_store.update_summary(sid, updated_summary)
    await session_store.touch_meta(sid)

    logger.info(
        "chat_turn_complete",
        session_id=sid,
        sources=sources,
        confidence=confidence,
        total_ms=round((time.monotonic() - t_start) * 1000),
    )

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
