from collections import Counter
from datetime import date

from fastapi import HTTPException
from rental_service.services.categories import get_categories_cached
from rental_service.services.central_api import chunked, fetch_all_pages
from rental_service.utils.dates import format_date, parse_iso_to_date
from rental_service.utils.heap import push_bounded
from rental_service.utils.intervals import (
    clip_interval,
    compute_free_windows,
    gap_length_days,
    longest_free_streak,
    merge_intervals,
    overlapping_busy_periods,
)
from rental_service.utils.validation import (
    require_date_range,
    require_month_range,
    require_positive_int,
    require_year,
)

from shared.app_core.central_api import CentralAPIClient

BATCH_SIZE = 50
MAX_MERGED_FEED_PRODUCTS = 10
MAX_MERGED_FEED_LIMIT = 100


def _category_rank_key(category: str) -> tuple[int, ...]:
    return (*(-ord(char) for char in category), 1)


def parse_merged_feed_product_ids(raw_product_ids: str) -> list[int]:
    parts = [part.strip() for part in raw_product_ids.split(",")]
    if not 1 <= len(parts) <= MAX_MERGED_FEED_PRODUCTS or any(part == "" for part in parts):
        raise HTTPException(
            status_code=400,
            detail="productIds must be 1-10 comma-separated integers",
        )

    product_ids: list[int] = []
    seen: set[int] = set()
    for part in parts:
        try:
            product_id = int(part)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="productIds must be 1-10 comma-separated integers",
            ) from exc
        if product_id <= 0:
            raise HTTPException(
                status_code=400,
                detail="productIds must be 1-10 comma-separated integers",
            )
        if product_id not in seen:
            seen.add(product_id)
            product_ids.append(product_id)

    return product_ids


def require_merged_feed_limit(value: int) -> int:
    if value <= 0 or value > MAX_MERGED_FEED_LIMIT:
        raise HTTPException(status_code=400, detail="limit must be a positive integer <= 100")
    return value


def _normalize_feed_rental(rental: dict) -> dict:
    rental_id = rental.get("id", rental.get("rentalId", 0))
    product_id = rental.get("productId", rental.get("product_id", 0))
    return {
        "rentalId": int(rental_id),
        "productId": int(product_id),
        "rentalStart": str(rental["rentalStart"])[:10],
        "rentalEnd": str(rental["rentalEnd"])[:10],
    }


def _feed_sort_key(item: dict) -> tuple[str, int, int]:
    return (
        str(item["rentalStart"]),
        int(item["productId"]),
        int(item["rentalId"]),
    )


def _merge_sorted_feeds(left: list[dict], right: list[dict], limit: int) -> list[dict]:
    merged: list[dict] = []
    left_index = 0
    right_index = 0

    while len(merged) < limit and left_index < len(left) and right_index < len(right):
        if _feed_sort_key(left[left_index]) <= _feed_sort_key(right[right_index]):
            merged.append(left[left_index])
            left_index += 1
        else:
            merged.append(right[right_index])
            right_index += 1

    while len(merged) < limit and left_index < len(left):
        merged.append(left[left_index])
        left_index += 1

    while len(merged) < limit and right_index < len(right):
        merged.append(right[right_index])
        right_index += 1

    return merged


def _merge_feed_groups(feeds: list[list[dict]], limit: int) -> list[dict]:
    if not feeds:
        return []
    if len(feeds) == 1:
        return feeds[0][:limit]

    midpoint = len(feeds) // 2
    left = _merge_feed_groups(feeds[:midpoint], limit)
    right = _merge_feed_groups(feeds[midpoint:], limit)
    return _merge_sorted_feeds(left, right, limit)


async def list_products(
    client: CentralAPIClient,
    *,
    category: str | None,
    page: str | None,
    limit: str | None,
    extra_params: dict[str, str] | None = None,
) -> dict:
    params = dict(extra_params or {})
    if category:
        categories = await get_categories_cached(client)
        if category not in categories.values:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": f"Invalid category '{category}'",
                    "validCategories": categories.ordered,
                },
            )
        params["category"] = category
    if page:
        params["page"] = page
    if limit:
        params["limit"] = limit
    return await client.get("/api/data/products", params=params)


async def get_product_availability(
    client: CentralAPIClient,
    *,
    product_id: int,
    from_date: str,
    to_date: str,
) -> dict:
    request_start, request_end = require_date_range(from_date, to_date)
    rentals = await fetch_all_pages(
        client,
        "/api/data/rentals",
        params={"product_id": str(product_id)},
    )

    intervals = [
        (
            parse_iso_to_date(str(rental["rentalStart"])),
            parse_iso_to_date(str(rental["rentalEnd"])),
        )
        for rental in rentals
    ]
    merged_busy = merge_intervals(intervals)
    busy_periods = overlapping_busy_periods(request_start, request_end, merged_busy)
    free_windows = compute_free_windows(request_start, request_end, merged_busy)

    return {
        "productId": product_id,
        "from": from_date,
        "to": to_date,
        "available": len(busy_periods) == 0,
        "busyPeriods": [
            {"start": format_date(start), "end": format_date(end)} for start, end in busy_periods
        ],
        "freeWindows": [
            {"start": format_date(start), "end": format_date(end)} for start, end in free_windows
        ],
    }


async def get_kth_busiest_date(
    client: CentralAPIClient,
    *,
    from_month: str,
    to_month: str,
    k: int,
) -> dict:
    require_positive_int(k, field_name="k")
    months = require_month_range(from_month, to_month)

    heap: list[tuple[int, int, str]] = []
    total_dates = 0

    for month in months:
        payload = await client.get(
            "/api/data/rentals/stats",
            params={"group_by": "date", "month": month},
        )
        rows = payload.get("data", [])
        for row in rows:
            row_date = parse_iso_to_date(str(row["date"]))
            item = (int(row["count"]), -row_date.toordinal(), format_date(row_date))
            push_bounded(heap, item, k)
            total_dates += 1

    if total_dates < k or not heap:
        raise HTTPException(status_code=404, detail="k exceeds the total number of distinct dates")

    count, _, kth_date = heap[0]
    return {
        "from": from_month,
        "to": to_month,
        "k": k,
        "date": kth_date,
        "rentalCount": count,
    }


async def get_user_top_categories(
    client: CentralAPIClient,
    *,
    user_id: int,
    k: int,
) -> dict:
    require_positive_int(k, field_name="k")
    rentals = await fetch_all_pages(
        client,
        "/api/data/rentals",
        params={"renter_id": str(user_id)},
    )
    if not rentals:
        return {"userId": user_id, "topCategories": []}

    product_ids = sorted({int(rental["productId"]) for rental in rentals})
    product_categories: dict[int, str] = {}

    async for batch in chunked(product_ids, BATCH_SIZE):
        payload = await client.get(
            "/api/data/products/batch",
            params={"ids": ",".join(str(product_id) for product_id in batch)},
        )
        for item in payload.get("data", []):
            product_categories[int(item["id"])] = str(item["category"])

    counts: Counter[str] = Counter()
    for rental in rentals:
        category = product_categories.get(int(rental["productId"]))
        if category is not None:
            counts[category] += 1

    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:k]
    return {
        "userId": user_id,
        "topCategories": [
            {"category": category, "rentalCount": count} for category, count in ranked
        ],
    }


async def get_longest_free_streak(
    client: CentralAPIClient,
    *,
    product_id: int,
    year: int,
) -> dict:
    require_year(year)
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)

    rentals = await fetch_all_pages(
        client,
        "/api/data/rentals",
        params={"product_id": str(product_id)},
    )

    intervals = []
    for rental in rentals:
        start = parse_iso_to_date(str(rental["rentalStart"]))
        end = parse_iso_to_date(str(rental["rentalEnd"]))
        clipped = clip_interval(start, end, year_start, year_end)
        if clipped is not None:
            intervals.append(clipped)

    merged_busy = merge_intervals(intervals)
    best_gap = longest_free_streak(year_start, year_end, merged_busy)
    if best_gap is None:
        return {
            "productId": product_id,
            "year": year,
            "longestFreeStreak": {"from": "", "to": "", "days": 0},
        }

    best_start, best_end = best_gap

    return {
        "productId": product_id,
        "year": year,
        "longestFreeStreak": {
            "from": format_date(best_start),
            "to": format_date(best_end),
            "days": gap_length_days((best_start, best_end)),
        },
    }


async def get_merged_feed(
    client: CentralAPIClient,
    *,
    product_ids: list[int],
    limit: int,
) -> dict:
    require_merged_feed_limit(limit)
    if not 1 <= len(product_ids) <= MAX_MERGED_FEED_PRODUCTS:
        raise HTTPException(status_code=400, detail="productIds must contain 1-10 integers")

    deduped_product_ids = list(dict.fromkeys(product_ids))

    feeds: list[list[dict]] = []
    for product_id in deduped_product_ids:
        rentals = await fetch_all_pages(
            client,
            "/api/data/rentals",
            params={"product_id": str(product_id)},
            max_items=limit,
        )
        feeds.append([_normalize_feed_rental(rental) for rental in rentals])

    return {
        "productIds": deduped_product_ids,
        "limit": limit,
        "feed": _merge_feed_groups(feeds, limit),
    }
