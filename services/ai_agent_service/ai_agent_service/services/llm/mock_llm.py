from ai_agent_service.schemas.chat import ChatResponse
from ai_agent_service.services.llm.base import BaseLLM
from ai_agent_service.services.rag.retriever import RetrievedDocument


class MockLLM(BaseLLM):
    def generate_answer(
        self,
        query: str,
        documents: list[RetrievedDocument],
        context: str,
    ) -> ChatResponse:
        if not documents:
            return ChatResponse(
                answer="Insufficient relevant context is available in the current knowledge base.",
                sources=[],
                confidence=0.15,
            )

        summary_parts = [document.snippet.rstrip(".") for document in documents[:2]]
        answer = " ".join(f"{part}." for part in summary_parts)
        confidence = round(min(0.9, 0.45 + 0.15 * len(documents[:2])), 2)
        return ChatResponse(
            answer=answer,
            sources=[document.source for document in documents],
            confidence=confidence,
        )
