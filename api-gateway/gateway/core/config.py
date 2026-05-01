from functools import lru_cache

from shared.app_core.config import CommonSettings


class GatewaySettings(CommonSettings):
    service_name: str = "api-gateway"
    service_port: int = 8000
    user_service_addr: str = "user-service:50051"
    rental_service_addr: str = "rental-service:50052"
    analytics_service_addr: str = "analytics-service:50053"
    agentic_service_addr: str = "agentic-service:50054"
    user_service_url: str = "http://user-service:8001"
    rental_service_url: str = "http://rental-service:8002"
    analytics_service_url: str = "http://analytics-service:8003"
    agentic_service_url: str = "http://agentic-service:8004"

    @property
    def service_registry(self) -> dict[str, str]:
        return {
            "user-service": self.user_service_url,
            "rental-service": self.rental_service_url,
            "analytics-service": self.analytics_service_url,
            "agentic-service": self.agentic_service_url,
        }


@lru_cache
def get_settings() -> GatewaySettings:
    return GatewaySettings()
