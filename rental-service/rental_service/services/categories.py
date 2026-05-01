import asyncio
import time
from dataclasses import dataclass

from shared.app_core.central_api import CentralAPIClient

CATEGORY_TTL_SECONDS = 60 * 30


@dataclass(slots=True)
class CategoriesSnapshot:
    ordered: list[str]
    values: set[str]


_cache: CategoriesSnapshot | None = None
_expires_at = 0.0
_lock = asyncio.Lock()


async def get_categories_cached(client: CentralAPIClient) -> CategoriesSnapshot:
    global _cache, _expires_at

    now = time.monotonic()
    if _cache is not None and now < _expires_at:
        return _cache

    async with _lock:
        now = time.monotonic()
        if _cache is not None and now < _expires_at:
            return _cache

        payload = await client.get("/api/data/categories")
        categories = payload.get("categories", [])
        ordered = [str(category) for category in categories]
        _cache = CategoriesSnapshot(ordered=ordered, values=set(ordered))
        _expires_at = now + CATEGORY_TTL_SECONDS
        return _cache
