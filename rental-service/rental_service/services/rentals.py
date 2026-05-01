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


def _category_rank_key(category: str) -> tuple[int, ...]:
    return (*(-ord(char) for char in category), 1)


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
