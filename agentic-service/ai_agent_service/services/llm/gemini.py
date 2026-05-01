import google.generativeai as genai
from ai_agent_service.services.llm.base import BaseLLM
from ai_agent_service.services.rag.retriever import RetrievedDocument

_SYSTEM = (
    "You are RentPi assistant, helping users find and rent tools and equipment. "
    "Answer concisely using the provided context. If you can't answer from context, say so."
)


class GeminiLLM(BaseLLM):
    def __init__(self, api_key: str) -> None:
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel("gemini-1.5-flash")

    async def generate_answer(
        self,
        query: str,
        documents: list[RetrievedDocument],
        context: str,
        history: list[dict] | None = None,
    ) -> tuple[str, list[str], float]:
        history_text = ""
        if history:
            lines = [f"{m['role'].upper()}: {m['content']}" for m in history[-6:]]
            history_text = "\n".join(lines) + "\n\n"

        prompt = f"{_SYSTEM}\n\nContext:\n{context}\n\n{history_text}User: {query}\nAssistant:"

        response = await self._model.generate_content_async(prompt)
        answer = response.text.strip()
        sources = [doc.source for doc in documents]
        return answer, sources, 0.85
