from ai_agent_service.services.llm.base import BaseLLM
from ai_agent_service.services.rag.retriever import RetrievedDocument


class MockLLM(BaseLLM):
    async def generate_answer(
        self,
        query: str,
        documents: list[RetrievedDocument],
        context: str,
        history: list[dict] | None = None,
    ) -> tuple[str, list[str], float]:
        if not documents:
            return (
                "Insufficient relevant context is available in the current knowledge base.",
                [],
                0.15,
            )

        summary_parts = [doc.snippet.rstrip(".") for doc in documents[:2]]
        answer = " ".join(f"{part}." for part in summary_parts)
        confidence = round(min(0.9, 0.45 + 0.15 * len(documents[:2])), 2)
        sources = [doc.source for doc in documents]
        return answer, sources, confidence
