from ai_agent_service.services.llm.base import BaseLLM
from ai_agent_service.services.rag.retriever import RetrievedDocument
from openai import AsyncOpenAI

_SYSTEM = (
    "You are RentPi assistant, helping users find and rent tools and equipment. "
    "Answer concisely using the provided context. If you can't answer from context, say so."
)


class OpenAILLM(BaseLLM):
    def __init__(self, api_key: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)

    async def generate_answer(
        self,
        query: str,
        documents: list[RetrievedDocument],
        context: str,
        history: list[dict] | None = None,
    ) -> tuple[str, list[str], float]:
        messages = [{"role": "system", "content": f"{_SYSTEM}\n\nContext:\n{context}"}]
        for msg in (history or [])[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": query})

        response = await self._client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,  # type: ignore[arg-type]
            max_tokens=512,
        )
        answer = response.choices[0].message.content or ""
        sources = [doc.source for doc in documents]
        return answer.strip(), sources, 0.85
