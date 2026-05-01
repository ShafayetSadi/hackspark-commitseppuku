from abc import ABC, abstractmethod

from ai_agent_service.schemas.chat import ChatResponse
from ai_agent_service.services.rag.retriever import RetrievedDocument


class BaseLLM(ABC):
    @abstractmethod
    def generate_answer(
        self,
        query: str,
        documents: list[RetrievedDocument],
        context: str,
    ) -> ChatResponse:
        raise NotImplementedError
