from ai_agent_service.services.llm.prompt_llm import PromptDrivenLLM
from openai import AsyncOpenAI

class OpenAILLM(PromptDrivenLLM):
    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def _complete_text(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
        )
        return (response.choices[0].message.content or "").strip()
