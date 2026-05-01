from functools import lru_cache

from shared.app_core.config import CommonSettings


class AnalyticsSettings(CommonSettings):
    service_name: str = "analytics-service"
    service_port: int = 8003
    grpc_port: int = 50053
    central_api_url: str = "https://technocracy.brittoo.xyz"
    central_api_token: str = ""


@lru_cache
def get_settings() -> AnalyticsSettings:
    return AnalyticsSettings()
