from collections.abc import AsyncIterator

from rental_service.core.config import RentalSettings

from shared.app_core.central_api import CentralAPIClient

DEFAULT_PAGE_LIMIT = 100


def get_central_client(settings: RentalSettings) -> CentralAPIClient:
    return CentralAPIClient(
        settings.central_api_url,
        settings.central_api_token,
        redis_url=settings.central_api_redis_url,
        max_calls=settings.central_api_rate_limit,
        window_seconds=settings.central_api_rate_window_seconds,
    )


async def fetch_all_pages(
    client: CentralAPIClient,
    path: str,
    params: dict[str, str] | None = None,
    *,
    page_limit: int = DEFAULT_PAGE_LIMIT,
) -> list[dict]:
    page = 1
    items: list[dict] = []
    base_params = dict(params or {})
    base_params.setdefault("limit", str(page_limit))

    while True:
        payload = await client.get(path, params={**base_params, "page": str(page)})
        batch = payload.get("data", [])
        if not isinstance(batch, list):
            return items

        items.extend(batch)

        total_pages = payload.get("totalPages")
        if isinstance(total_pages, int):
            if page >= total_pages:
                break
        else:
            total = payload.get("total")
            if isinstance(total, int) and len(items) >= total:
                break
            if len(batch) < int(base_params["limit"]):
                break

        page += 1

    return items


def chunked(values: list[int], size: int) -> AsyncIterator[list[int]]:
    async def iterator() -> AsyncIterator[list[int]]:
        for index in range(0, len(values), size):
            yield values[index : index + size]

    return iterator()
