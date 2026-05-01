import re

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
            product_id = _extract_product_id(lowered)
            from_date = _extract_date(lowered, "from")
            to_date = _extract_date(lowered, "to")
            args: dict[str, str] = {}
            if product_id:
                args["product_id"] = product_id
            if from_date:
                args["from_date"] = from_date
            if to_date:
                args["to_date"] = to_date
            missing = [f for f in ("product_id", "from_date", "to_date") if f not in args]
            if missing:
                if "product_id" in missing:
                    q = "Which product would you like to check availability for, and over what dates?"
                else:
                    q = f"What date range should I check for product {product_id}? (e.g. 2024-06-01 to 2024-06-30)"
                return ToolDecision("get_availability", args, clarification=q)
            return ToolDecision("get_availability", args)

        if "peak" in lowered or "busiest" in lowered:
            from_month = _extract_month(lowered, "from")
            to_month = _extract_month(lowered, "to")
            args = {}
            if from_month:
                args["from_month"] = from_month
            if to_month:
                args["to_month"] = to_month
            if not from_month or not to_month:
                return ToolDecision(
                    "get_peak_window", args,
                    clarification="What month range are you interested in for the peak window? (e.g. 2024-01 to 2024-06)",
                )
            return ToolDecision("get_peak_window", args)

        if "surge" in lowered or "spike" in lowered:
            month = _extract_month(lowered, "any")
            if not month:
                return ToolDecision(
                    "get_surge_days", {},
                    clarification="Which month should I pull surge data for? (e.g. 2024-06)",
                )
            return ToolDecision("get_surge_days", {"month": month})

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


def _extract_product_id(message: str) -> str:
    match = re.search(r"\bproduct\s+(\d+)\b|\bid[:\s]+(\d+)\b|#(\d+)", message)
    if match:
        return next(g for g in match.groups() if g is not None)
    bare = re.search(r"\b(\d+)\b", message)
    return bare.group(1) if bare else ""


def _extract_date(message: str, _position: str) -> str:
    matches = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", message)
    if not matches:
        return ""
    if _position == "from":
        return matches[0]
    if _position == "to" and len(matches) >= 2:
        return matches[1]
    return ""


def _extract_month(message: str, _position: str) -> str:
    matches = re.findall(r"\b(\d{4}-\d{2})\b", message)
    if not matches:
        return ""
    if _position in ("from", "any"):
        return matches[0]
    if _position == "to" and len(matches) >= 2:
        return matches[1]
    return ""
