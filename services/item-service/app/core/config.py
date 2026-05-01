from functools import lru_cache

from shared.app_core.config import CommonSettings


class ItemSettings(CommonSettings):
    service_name: str = "item-service"
    service_port: int = 8000
    default_page_size: int = 20
    max_page_size: int = 100


@lru_cache
def get_settings() -> ItemSettings:
    return ItemSettings()
