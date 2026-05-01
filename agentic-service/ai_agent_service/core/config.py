from functools import lru_cache

from shared.app_core.config import CommonSettings


class AIAgentSettings(CommonSettings):
    service_name: str = "agentic-service"
    service_port: int = 8004
    grpc_port: int = 50054
    rental_service_addr: str = "rental-service:50052"
    analytics_service_addr: str = "analytics-service:50053"
    llm_provider: str = "mock"
    min_relevance_score: float = 0.2
    redis_url: str = "redis://redis:6379/0"
    redis_session_ttl_seconds: int = 0
    chat_recent_messages_limit: int = 5
    summary_message_window: int = 8
    gemini_api_key: str = ""
    openai_api_key: str = ""
    groq_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_model: str = "gemini-2.5-flash"
    groq_model: str = "llama-3.1-8b-instant"
    central_api_url: str = "https://technocracy.brittoo.xyz"
    central_api_token: str = ""


@lru_cache
def get_settings() -> AIAgentSettings:
    return AIAgentSettings()
