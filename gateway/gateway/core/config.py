from functools import lru_cache

from shared.app_core.config import CommonSettings


class GatewaySettings(CommonSettings):
    service_name: str = "api-gateway"
    service_port: int = 8000
    auth_service_url: str = "http://auth-service:8000"
    item_service_url: str = "http://item-service:8000"
    ai_agent_service_url: str = "http://ai-agent-service:8000"

    @property
    def service_registry(self) -> dict[str, str]:
        return {
            "auth": self.auth_service_url,
            "items": self.item_service_url,
            "ai": self.ai_agent_service_url,
        }


@lru_cache
def get_settings() -> GatewaySettings:
    return GatewaySettings()
