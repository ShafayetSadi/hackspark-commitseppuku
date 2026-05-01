from functools import lru_cache

from shared.app_core.config import CommonSettings


class AIAgentSettings(CommonSettings):
    service_name: str = "ai-agent-service"
    service_port: int = 8000
    llm_provider: str = "mock"
    min_relevance_score: float = 0.2


@lru_cache
def get_settings() -> AIAgentSettings:
    return AIAgentSettings()
