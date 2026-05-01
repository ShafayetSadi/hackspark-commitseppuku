from functools import lru_cache

from shared.app_core.config import CommonSettings


class AuthSettings(CommonSettings):
    service_name: str = "auth-service"
    service_port: int = 8000


@lru_cache
def get_settings() -> AuthSettings:
    return AuthSettings()
