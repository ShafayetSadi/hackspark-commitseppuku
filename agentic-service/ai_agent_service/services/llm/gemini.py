import google.generativeai as genai
from ai_agent_service.services.llm.prompt_llm import PromptDrivenLLM


class GeminiLLM(PromptDrivenLLM):
    def __init__(self, api_key: str, model: str) -> None:
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)

    async def _complete_text(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        prompt = f"{system_prompt}\n\n{user_prompt}\n\nLimit your response to about {max_tokens} tokens."
        response = await self._model.generate_content_async(prompt)
        return response.text.strip()
