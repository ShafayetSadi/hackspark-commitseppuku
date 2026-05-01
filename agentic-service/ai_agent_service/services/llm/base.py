from abc import ABC, abstractmethod

from ai_agent_service.services.rag.retriever import RetrievedDocument


class BaseLLM(ABC):
    @abstractmethod
    async def generate_answer(
        self,
        query: str,
        documents: list[RetrievedDocument],
        context: str,
        history: list[dict] | None = None,
    ) -> tuple[str, list[str], float]:
        """Return (answer, sources, confidence)."""
        raise NotImplementedError
