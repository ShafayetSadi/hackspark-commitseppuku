from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ToolDecision:
    tool_name: str | None
    arguments: dict[str, str]
    clarification: str | None = None


class BaseLLM(ABC):
    @abstractmethod
    async def generate_session_title(self, first_message: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def decide_tool(
        self,
        session_summary: str,
        recent_messages: list[dict],
        current_message: str,
        tools: list[dict],
    ) -> ToolDecision:
        raise NotImplementedError

    @abstractmethod
    async def generate_final_answer(
        self,
        session_summary: str,
        recent_messages: list[dict],
        current_message: str,
        tool_result: dict | None,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def summarize_session(
        self,
        current_summary: str,
        recent_messages: list[dict],
    ) -> str:
        raise NotImplementedError
