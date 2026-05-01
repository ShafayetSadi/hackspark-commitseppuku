"""Analytics computations over Central API product and rental data."""

import heapq
from collections import Counter
from collections.abc import Iterable
from datetime import date, timedelta

from fastapi import HTTPException

from shared.app_core.central_api import CentralAPIClient

WINDOW_DAYS = 7
SEASONAL_WINDOW_RADIUS_DAYS = 7
PAST_SEASONAL_YEARS = 2
MAX_RECOMMENDATIONS_LIMIT = 50
PRODUCT_BATCH_SIZE = 50
MAX_RECOMMENDATION_PAGES_PER_WINDOW = 9
RECOMMENDATIONS_PAGE_BUDGET_DETAIL = (
    "Exact seasonal recommendations exceed the safe Central API page budget for live data"
)


async def _fetch_all_products(client: CentralAPIClient) -> list[dict]:
    """Best-effort fetch — returns whatever the Central API provides."""
    try:
        result = await client.get("/api/data/products")
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            for key in ("data", "results", "items", "products"):
                if isinstance(result.get(key), list):
                    return result[key]
        return []
    except Exception:
        return []


async def _fetch_all_pages(
    client: CentralAPIClient,
    path: str,
    params: dict[str, str] | None = None,
    *,
    page_limit: int = 100,
    max_total_pages: int | None = None,
    max_pages_error_detail: str | None = None,
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
            if max_total_pages is not None and total_pages > max_total_pages:
                raise HTTPException(
                    status_code=503,
                    detail=max_pages_error_detail or "Upstream page budget exceeded",
                )
            if page >= total_pages:
                break
        else:
            total = payload.get("total")
            if isinstance(total, int) and len(items) >= total:
                break
            if len(batch) < int(base_params["limit"]):
                break

        if max_total_pages is not None and page >= max_total_pages:
            raise HTTPException(
                status_code=503,
                detail=max_pages_error_detail or "Upstream page budget exceeded",
            )

        page += 1

    return items


def _chunked(values: list[int], size: int) -> Iterable[list[int]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


def _parse_yyyy_mm_dd(value: str) -> date:
    if len(value) != 10:
        raise HTTPException(status_code=400, detail="Invalid date format; expected YYYY-MM-DD")

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format; expected YYYY-MM-DD",
        ) from exc


def _require_recommendation_limit(value: int) -> int:
    if value <= 0 or value > MAX_RECOMMENDATIONS_LIMIT:
        raise HTTPException(
            status_code=400,
            detail="limit must be a positive integer <= 50",
        )
    return value


def _shift_year(anchor: date, years: int) -> date:
    try:
        return anchor.replace(year=anchor.year + years)
    except ValueError:
        if anchor.month == 2 and anchor.day == 29:
            return anchor.replace(year=anchor.year + years, day=28)
        raise


def _parse_iso_day(value: str) -> date:
    return date.fromisoformat(value[:10])


def _parse_year_month(value: str) -> tuple[int, int]:
    parts = value.split("-", maxsplit=1)
    if len(parts) != 2 or len(parts[0]) != 4 or len(parts[1]) != 2:
        raise HTTPException(status_code=400, detail="Invalid month format; expected YYYY-MM")

    try:
        year = int(parts[0])
        month = int(parts[1])
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="Invalid month format; expected YYYY-MM"
        ) from exc

    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Invalid month value; expected 01-12")

    return year, month


def _month_start(value: str) -> date:
    year, month = _parse_year_month(value)
    return date(year, month, 1)


def _month_end(value: str) -> date:
    year, month = _parse_year_month(value)
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def _month_days(value: str) -> list[date]:
    start = _month_start(value)
    end = _month_end(value)
    days: list[date] = []
    cursor = start
    while cursor <= end:
        days.append(cursor)
        cursor += timedelta(days=1)
    return days


def _iter_month_strings(from_month: str, to_month: str) -> list[str]:
    year, month = _parse_year_month(from_month)
    end_year, end_month = _parse_year_month(to_month)
    months: list[str] = []
    while (year, month) <= (end_year, end_month):
        months.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            month = 1
            year += 1
    return months


def _validate_peak_window_range(from_month: str, to_month: str) -> tuple[date, date, list[str]]:
    start = _month_start(from_month)
    end = _month_end(to_month)
    if start > end:
        raise HTTPException(status_code=400, detail="'from' must not be after 'to'")

    months = _iter_month_strings(from_month, to_month)
    if len(months) > 12:
        raise HTTPException(status_code=400, detail="Month range must not exceed 12 months")

    if (end - start).days + 1 < WINDOW_DAYS:
        raise HTTPException(status_code=400, detail="Not enough data for a 7-day window")

    return start, end, months


def _coerce_stats_rows(payload: dict) -> list[dict]:
    rows = payload.get("data", [])
    return rows if isinstance(rows, list) else []


async def compute_trends(client: CentralAPIClient, category: str | None) -> dict:
    products = await _fetch_all_products(client)

    if category:
        products = [p for p in products if str(p.get("category", "")).lower() == category.lower()]

    category_counts: Counter = Counter()
    for product in products:
        cat = str(product.get("category", "unknown"))
        category_counts[cat] += 1

    return {
        "total_products": len(products),
        "by_category": dict(category_counts.most_common()),
        "top_categories": [cat for cat, _ in category_counts.most_common(5)],
    }


async def compute_surge(client: CentralAPIClient, category: str | None) -> dict:
    products = await _fetch_all_products(client)

    category_counts: Counter = Counter()
    for product in products:
        cat = str(product.get("category", "unknown"))
        category_counts[cat] += 1

    if not category_counts:
        return {"surge_detected": False, "categories": []}

    avg = sum(category_counts.values()) / len(category_counts)
    threshold = avg * 1.5

    surge_cats = [
        {"category": cat, "count": count, "surge_factor": round(count / avg, 2)}
        for cat, count in category_counts.items()
        if count >= threshold
    ]

    if category:
        surge_cats = [s for s in surge_cats if s["category"].lower() == category.lower()]

    return {
        "surge_detected": len(surge_cats) > 0,
        "average_per_category": round(avg, 2),
        "surge_threshold": round(threshold, 2),
        "categories": sorted(surge_cats, key=lambda x: -x["count"]),
    }


async def compute_recommendations(
    client: CentralAPIClient,
    *,
    target_date: str,
    limit: int,
) -> dict:
    anchor_day = _parse_yyyy_mm_dd(target_date)
    limit = _require_recommendation_limit(limit)

    seasonal_counts: Counter[int] = Counter()

    for years_ago in range(1, PAST_SEASONAL_YEARS + 1):
        seasonal_anchor = _shift_year(anchor_day, -years_ago)
        window_start = seasonal_anchor - timedelta(days=SEASONAL_WINDOW_RADIUS_DAYS)
        window_end = seasonal_anchor + timedelta(days=SEASONAL_WINDOW_RADIUS_DAYS)
        rentals = await _fetch_all_pages(
            client,
            "/api/data/rentals",
            params={"from": window_start.isoformat(), "to": window_end.isoformat()},
            max_total_pages=MAX_RECOMMENDATION_PAGES_PER_WINDOW,
            max_pages_error_detail=RECOMMENDATIONS_PAGE_BUDGET_DETAIL,
        )

        for rental in rentals:
            rental_start_raw = rental.get("rentalStart")
            product_id_raw = rental.get("productId")
            if rental_start_raw is None or product_id_raw is None:
                continue

            try:
                rental_start = _parse_iso_day(str(rental_start_raw))
                product_id = int(product_id_raw)
            except (TypeError, ValueError):
                continue

            if window_start <= rental_start <= window_end:
                seasonal_counts[product_id] += 1

    if not seasonal_counts:
        return {"date": target_date, "recommendations": []}

    top_items = heapq.nlargest(
        limit,
        seasonal_counts.items(),
        key=lambda item: (item[1], -item[0]),
    )
    ranked_product_ids = [product_id for product_id, _score in top_items]

    product_details: dict[int, dict] = {}
    for product_batch in _chunked(ranked_product_ids, PRODUCT_BATCH_SIZE):
        payload = await client.get(
            "/api/data/products/batch",
            params={"ids": ",".join(str(product_id) for product_id in product_batch)},
        )
        for product in payload.get("data", []):
            try:
                product_details[int(product["id"])] = product
            except (KeyError, TypeError, ValueError):
                continue

    recommendations: list[dict] = []
    for product_id in ranked_product_ids:
        product = product_details.get(product_id, {})
        recommendations.append(
            {
                "productId": product_id,
                "name": str(product.get("name", f"Product #{product_id}")),
                "category": str(product.get("category", "UNKNOWN")),
                "score": seasonal_counts[product_id],
            }
        )

    return {
        "date": target_date,
        "recommendations": recommendations,
    }


async def compute_peak_window(
    client: CentralAPIClient,
    *,
    from_month: str,
    to_month: str,
) -> dict:
    start, end, months = _validate_peak_window_range(from_month, to_month)

    daily_counts: dict[date, int] = {}
    for month in months:
        payload = await client.get(
            "/api/data/rentals/stats",
            params={"group_by": "date", "month": month},
        )
        for row in _coerce_stats_rows(payload):
            row_date = date.fromisoformat(str(row["date"])[:10])
            if start <= row_date <= end:
                daily_counts[row_date] = daily_counts.get(row_date, 0) + int(row["count"])

    all_days: list[date] = []
    cursor = start
    while cursor <= end:
        all_days.append(cursor)
        cursor += timedelta(days=1)

    running_total = sum(daily_counts.get(day, 0) for day in all_days[:WINDOW_DAYS])
    best_total = running_total
    best_start_index = 0

    for right_index in range(WINDOW_DAYS, len(all_days)):
        entering_day = all_days[right_index]
        leaving_day = all_days[right_index - WINDOW_DAYS]
        running_total += daily_counts.get(entering_day, 0)
        running_total -= daily_counts.get(leaving_day, 0)
        if running_total > best_total:
            best_total = running_total
            best_start_index = right_index - WINDOW_DAYS + 1

    best_start = all_days[best_start_index]
    best_end = all_days[best_start_index + WINDOW_DAYS - 1]

    return {
        "from": from_month,
        "to": to_month,
        "peakWindow": {
            "from": best_start.isoformat(),
            "to": best_end.isoformat(),
            "totalRentals": best_total,
        },
    }


async def compute_surge_days(client: CentralAPIClient, *, month: str) -> dict:
    month_start = _month_start(month)
    month_end = _month_end(month)
    month_days = _month_days(month)

    payload = await client.get(
        "/api/data/rentals/stats",
        params={"group_by": "date", "month": month},
    )

    daily_counts = {day: 0 for day in month_days}
    for row in _coerce_stats_rows(payload):
        row_date = date.fromisoformat(str(row["date"])[:10])
        if month_start <= row_date <= month_end:
            daily_counts[row_date] = daily_counts.get(row_date, 0) + int(row["count"])

    data = [
        {
            "date": day.isoformat(),
            "count": daily_counts[day],
            "nextSurgeDate": None,
            "daysUntil": None,
        }
        for day in month_days
    ]

    waiting_days: list[int] = []
    for current_index, day in enumerate(month_days):
        current_count = daily_counts[day]
        while waiting_days and current_count > data[waiting_days[-1]]["count"]:
            previous_index = waiting_days.pop()
            previous_day = month_days[previous_index]
            data[previous_index]["nextSurgeDate"] = day.isoformat()
            data[previous_index]["daysUntil"] = (day - previous_day).days
        waiting_days.append(current_index)

    return {
        "month": month,
        "data": data,
    }
