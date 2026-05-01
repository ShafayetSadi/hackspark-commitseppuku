from ai_agent_service.services.llm.base import BaseLLM, ToolDecision


class MockLLM(BaseLLM):
    async def generate_session_title(self, first_message: str) -> str:
        words = [word.strip(".,!?") for word in first_message.split() if word.strip(".,!?")]
        if not words:
            return "Untitled Chat"
        return " ".join(word.capitalize() for word in words[:4])

    async def decide_tool(
        self,
        session_summary: str,
        recent_messages: list[dict],
        current_message: str,
        tools: list[dict],
    ) -> ToolDecision:
        lowered = current_message.lower()
        if "recommend" in lowered:
            return ToolDecision("get_recommendations", {"category": _extract_category(lowered)})
        if "availability" in lowered or "available" in lowered:
            return ToolDecision("get_availability", {"subject": _extract_category(lowered)})
        if "peak" in lowered or "busiest" in lowered:
            return ToolDecision("get_peak_window", {"category": _extract_category(lowered)})
        if "surge" in lowered or "spike" in lowered:
            return ToolDecision("get_surge_days", {"category": _extract_category(lowered)})
        if any(keyword in lowered for keyword in ("top category", "best category", "growing", "growth")):
            return ToolDecision("get_top_category", {"region": _extract_category(lowered)})
        return ToolDecision(None, {})

    async def generate_final_answer(
        self,
        session_summary: str,
        recent_messages: list[dict],
        current_message: str,
        tool_result: dict | None,
    ) -> str:
        if not tool_result:
            return (
                "I can help analyze rental demand, availability, surge patterns, and recommendations. "
                "Ask about a category like tools, electronics, or outdoor gear for a grounded answer."
            )

        tool_name = tool_result["tool_name"]
        result = tool_result["result"]
        if tool_name == "get_recommendations":
            recs = ", ".join(result["recommendations"])
            return (
                f"For {result['category']}, the strongest next picks are {recs}. "
                f"{result['note']}"
            )
        if tool_name == "get_availability":
            return (
                f"{result['subject']} is currently at {result['availability']}. "
                f"Expected restock timing is {result['restock_eta']}."
            )
        if tool_name == "get_peak_window":
            return (
                f"The busiest rental window for {result['category']} is {result['peak_window']}. "
                f"{result['note']}"
            )
        if tool_name == "get_surge_days":
            return (
                f"{result['category']} shows the strongest demand surges on {result['surge_days']}. "
                f"{result['note']}"
            )
        return (
            f"{result['top_category']} is leading at roughly {result['market_share']}. "
            f"{result['note']}"
        )

    async def summarize_session(
        self,
        current_summary: str,
        recent_messages: list[dict],
    ) -> str:
        recent_lines = [f"{msg['role']}: {msg['content']}" for msg in recent_messages[-4:]]
        if not recent_lines:
            return current_summary or "No conversation yet."
        return "\n".join(recent_lines[:6])


def _extract_category(message: str) -> str:
    for category in ("tools", "electronics", "outdoor"):
        if category in message:
            return category
    return "tools"
