from functools import lru_cache

from shared.app_core.config import CommonSettings


class AuthSettings(CommonSettings):
    service_name: str = "user-service"
    service_port: int = 8001
    grpc_port: int = 50051
    central_api_url: str = "https://technocracy.brittoo.xyz"
    central_api_token: str = ""


@lru_cache
def get_settings() -> AuthSettings:
    return AuthSettings()
