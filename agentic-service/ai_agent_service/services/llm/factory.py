"""LLM provider factory — selects backend from LLM_PROVIDER env setting."""

from ai_agent_service.core.config import AIAgentSettings
from ai_agent_service.services.llm.base import BaseLLM
from ai_agent_service.services.llm.mock_llm import MockLLM


def get_llm(settings: AIAgentSettings) -> BaseLLM:
    provider = settings.llm_provider.lower()

    if provider == "gemini":
        from ai_agent_service.services.llm.gemini import GeminiLLM

        return GeminiLLM(settings.gemini_api_key)

    if provider == "openai":
        from ai_agent_service.services.llm.openai_llm import OpenAILLM

        return OpenAILLM(settings.openai_api_key)

    if provider == "groq":
        from ai_agent_service.services.llm.groq_llm import GroqLLM

        return GroqLLM(settings.groq_api_key)

    return MockLLM()
