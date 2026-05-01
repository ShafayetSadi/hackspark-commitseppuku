from functools import lru_cache

from shared.app_core.config import CommonSettings


class AIAgentSettings(CommonSettings):
    service_name: str = "agentic-service"
    service_port: int = 8004
    grpc_port: int = 50054
    llm_provider: str = "mock"
    min_relevance_score: float = 0.2
    mongo_uri: str = "mongodb://mongodb:27017/rentpi_agentic"
    gemini_api_key: str = ""
    openai_api_key: str = ""
    groq_api_key: str = ""
    central_api_url: str = "https://technocracy.brittoo.xyz"
    central_api_token: str = ""


@lru_cache
def get_settings() -> AIAgentSettings:
    return AIAgentSettings()
