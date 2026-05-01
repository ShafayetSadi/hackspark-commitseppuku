from functools import lru_cache

from shared.app_core.config import CommonSettings


class RentalSettings(CommonSettings):
    service_name: str = "rental-service"
    service_port: int = 8002
    grpc_port: int = 50052
    central_api_url: str = "https://technocracy.brittoo.xyz"
    central_api_token: str = ""


@lru_cache
def get_settings() -> RentalSettings:
    return RentalSettings()
