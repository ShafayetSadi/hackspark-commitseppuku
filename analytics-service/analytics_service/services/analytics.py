"""Analytics computations over Central API product data."""

from collections import Counter
from datetime import date, timedelta

from fastapi import HTTPException

from shared.app_core.central_api import CentralAPIClient

WINDOW_DAYS = 7


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
    client: CentralAPIClient, category: str | None, limit: int
) -> dict:
    products = await _fetch_all_products(client)

    if category:
        products = [p for p in products if str(p.get("category", "")).lower() == category.lower()]

    # Score products by availability field if present, otherwise by position
    def score(p: dict) -> float:
        avail = p.get("availability", p.get("quantity", p.get("stock", 1)))
        try:
            return float(avail)
        except (TypeError, ValueError):
            return 1.0

    ranked = sorted(products, key=score, reverse=True)
    top = ranked[: max(1, limit)]

    return {
        "total_candidates": len(products),
        "recommendations": top,
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
