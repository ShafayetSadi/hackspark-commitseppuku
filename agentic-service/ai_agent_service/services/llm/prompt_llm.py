from __future__ import annotations

import json
from abc import abstractmethod

from ai_agent_service.services.llm.base import BaseLLM, ToolDecision

_SYSTEM_PROMPT = (
    "You are RentPi assistant. Keep answers concise, practical, and grounded in the provided "
    "session summary, recent messages, and tool results. Never expose chain-of-thought."
)


class PromptDrivenLLM(BaseLLM):
    @abstractmethod
    async def _complete_text(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        raise NotImplementedError

    async def generate_session_title(self, first_message: str) -> str:
        prompt = (
            "Generate a 3 to 5 word title for this chat. "
            "Return only the title with no punctuation unless needed.\n\n"
            f"Message:\n{first_message}"
        )
        title = await self._complete_text(_SYSTEM_PROMPT, prompt, max_tokens=24)
        return self._sanitize_title(title)

    async def decide_tool(
        self,
        session_summary: str,
        recent_messages: list[dict],
        current_message: str,
        tools: list[dict],
    ) -> ToolDecision:
        prompt = (
            "Decide whether a tool is needed for the current user message.\n"
            "Return JSON only with this exact shape:\n"
            '{"tool_name": string|null, "arguments": object}\n\n'
            "Choose a tool only when external rental analytics or availability data is needed.\n"
            "If no tool is needed, return {\"tool_name\": null, \"arguments\": {}}.\n\n"
            f"SESSION SUMMARY:\n{session_summary or 'No summary yet.'}\n\n"
            f"RECENT MESSAGES:\n{_render_messages(recent_messages)}\n\n"
            f"CURRENT MESSAGE:\n{current_message}\n\n"
            f"TOOLS:\n{json.dumps(tools)}"
        )
        raw = await self._complete_text(_SYSTEM_PROMPT, prompt, max_tokens=180)
        data = _extract_json_object(raw)
        tool_name = data.get("tool_name")
        arguments = data.get("arguments", {})
        return ToolDecision(
            tool_name=tool_name if isinstance(tool_name, str) and tool_name else None,
            arguments=arguments if isinstance(arguments, dict) else {},
        )

    async def generate_final_answer(
        self,
        session_summary: str,
        recent_messages: list[dict],
        current_message: str,
        tool_result: dict | None,
    ) -> str:
        prompt = (
            f"SESSION SUMMARY:\n{session_summary or 'No summary yet.'}\n\n"
            f"RECENT MESSAGES:\n{_render_messages(recent_messages)}\n\n"
            f"CURRENT MESSAGE:\n{current_message}\n\n"
            "TOOL RESULT:\n"
            f"{json.dumps(tool_result) if tool_result else 'No tool used.'}\n\n"
            "Write the final assistant answer for the user. "
            "Do not dump raw JSON. If tool data exists, synthesize it into a helpful response."
        )
        answer = await self._complete_text(_SYSTEM_PROMPT, prompt, max_tokens=320)
        return answer.strip()

    async def summarize_session(
        self,
        current_summary: str,
        recent_messages: list[dict],
    ) -> str:
        prompt = (
            "Summarize this conversation in 4 to 6 short lines.\n"
            "Keep user intent, categories, important numbers, and decisions.\n"
            "Do not include headings.\n\n"
            f"CURRENT SUMMARY:\n{current_summary or 'No summary yet.'}\n\n"
            f"MESSAGES:\n{_render_messages(recent_messages)}"
        )
        summary = await self._complete_text(_SYSTEM_PROMPT, prompt, max_tokens=220)
        return summary.strip()

    def _sanitize_title(self, raw_title: str) -> str:
        title = raw_title.strip().strip("\"'")
        if not title:
            return "Untitled Chat"
        words = title.split()
        return " ".join(words[:5])


def _render_messages(messages: list[dict]) -> str:
    if not messages:
        return "No recent messages."
    return "\n".join(f"{msg['role'].upper()}: {msg['content']}" for msg in messages)


def _extract_json_object(raw: str) -> dict:
    candidate = raw.strip()
    if candidate.startswith("```"):
        lines = [line for line in candidate.splitlines() if not line.startswith("```")]
        candidate = "\n".join(lines).strip()

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end < start:
        return {"tool_name": None, "arguments": {}}

    try:
        return json.loads(candidate[start : end + 1])
    except json.JSONDecodeError:
        return {"tool_name": None, "arguments": {}}
