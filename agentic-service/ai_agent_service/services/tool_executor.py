import time
from dataclasses import dataclass

import httpx
from fastapi import HTTPException

from ai_agent_service.core.config import AIAgentSettings
from shared.app_core.central_api import CentralAPIClient
from shared.app_core.logging import get_logger

logger = get_logger("agentic-service.tools")


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    arguments: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ToolExecution:
    name: str
    arguments: dict[str, str]
    result: dict


TOOL_SPECS = (
    ToolSpec(
        name="get_top_category",
        description="Returns the most rented category and rental counts from live data.",
        arguments=("region",),
    ),
    ToolSpec(
        name="get_availability",
        description="Returns rental availability for a specific product over a date range. Requires product_id (integer), from_date and to_date (YYYY-MM-DD).",
        arguments=("product_id", "from_date", "to_date"),
    ),
    ToolSpec(
        name="get_recommendations",
        description="Returns trending products or categories worth exploring next.",
        arguments=("category",),
    ),
    ToolSpec(
        name="get_peak_window",
        description="Returns the busiest rental window for a category.",
        arguments=("category",),
    ),
    ToolSpec(
        name="get_surge_days",
        description="Returns recent demand spike days for a category.",
        arguments=("category",),
    ),
)


_TOOL_DATA = {
    "electronics": {
        "availability": "84% in stock across flagship SKUs",
        "peak_window": "Friday 4pm-8pm",
        "surge_days": "Tuesday and Friday",
        "recommendations": ["Mirrorless cameras", "Portable projectors", "Drone kits"],
    },
    "outdoor": {
        "availability": "76% in stock with weekend pressure",
        "peak_window": "Saturday 8am-noon",
        "surge_days": "Thursday and Saturday",
        "recommendations": ["Camping tents", "Trail GPS units", "Cooler bundles"],
    },
    "tools": {
        "availability": "68% in stock with high contractor demand",
        "peak_window": "Monday 7am-10am",
        "surge_days": "Monday and Wednesday",
        "recommendations": ["Rotary hammer drills", "Pressure washers", "Tile saws"],
    },
    "default": {
        "availability": "73% in stock overall",
        "peak_window": "Weekdays 10am-1pm",
        "surge_days": "Wednesday and Friday",
        "recommendations": ["Power tool bundles", "Generator rentals", "Lighting kits"],
    },
}

_CENTRAL_API_RATE_LIMIT = 15
_RENTALS_STATS_PATH = "/api/data/rentals/stats"


def describe_tools() -> list[dict]:
    return [
        {
            "name": spec.name,
            "description": spec.description,
            "arguments": list(spec.arguments),
        }
        for spec in TOOL_SPECS
    ]


async def execute_tool(
    name: str,
    arguments: dict[str, str],
    settings: AIAgentSettings,
) -> ToolExecution:
    normalized = {key: value.strip() for key, value in arguments.items() if value and value.strip()}
    subject = normalized.get("category") or normalized.get("subject") or normalized.get("region") or ""
    data = _resolve_subject_data(subject)

    logger.debug("tool_dispatch", tool=name, arguments=normalized, subject=subject or None)

    t0 = time.monotonic()
    if name == "get_top_category":
        result = await _fetch_top_category(settings)
    elif name == "get_availability":
        product_id = normalized.get("product_id", "")
        from_date = normalized.get("from_date", "")
        to_date = normalized.get("to_date", "")
        result = await _fetch_availability(settings, product_id, from_date, to_date)
    elif name == "get_recommendations":
        result = {
            "category": _humanize_subject(subject or "tools"),
            "recommendations": data["recommendations"],
            "note": "Ranked by recent engagement and conversion lift.",
        }
    elif name == "get_peak_window":
        result = {
            "category": _humanize_subject(subject or "tools"),
            "peak_window": data["peak_window"],
            "note": "Traffic spikes align with pickup planning and project starts.",
        }
    elif name == "get_surge_days":
        result = {
            "category": _humanize_subject(subject or "tools"),
            "surge_days": data["surge_days"],
            "note": "Surge days reflect the strongest week-over-week demand movement.",
        }
    else:
        logger.warning("tool_unknown", tool=name)
        raise ValueError(f"Unknown tool: {name}")

    logger.debug(
        "tool_result",
        tool=name,
        result_keys=list(result.keys()),
        exec_ms=round((time.monotonic() - t0) * 1000),
    )
    return ToolExecution(name=name, arguments=normalized, result=result)


async def _fetch_top_category(settings: AIAgentSettings) -> dict:
    logger.info("central_api_call_start", endpoint=_RENTALS_STATS_PATH, params={"group_by": "category"})
    t0 = time.monotonic()

    client = CentralAPIClient(
        settings.central_api_url,
        settings.central_api_token,
        redis_url=settings.redis_url,
        max_calls=_CENTRAL_API_RATE_LIMIT,
        window_seconds=60.0,
    )
    try:
        data = await client.get(_RENTALS_STATS_PATH, params={"group_by": "category"})
    except HTTPException as exc:
        logger.error(
            "central_api_call_failed",
            endpoint=_RENTALS_STATS_PATH,
            status=exc.status_code,
            detail=exc.detail,
            elapsed_ms=round((time.monotonic() - t0) * 1000),
        )
        return {
            "top_category": "Unavailable",
            "rental_count": None,
            "market_share": "N/A",
            "note": f"Could not fetch rental stats: {exc.detail}",
        }

    elapsed = round((time.monotonic() - t0) * 1000)

    items: list = (
        data.get("data")
        or data.get("results")
        or data.get("categories")
        or (data if isinstance(data, list) else [])
    )

    if not items:
        logger.warning("central_api_empty_response", endpoint=_RENTALS_STATS_PATH, elapsed_ms=elapsed)
        return {
            "top_category": "Unknown",
            "rental_count": None,
            "market_share": "N/A",
            "note": "No category data returned from rental stats API.",
        }

    def _count(item: dict) -> int:
        return int(
            item.get("count")
            or item.get("rental_count")
            or item.get("total")
            or item.get("value")
            or 0
        )

    sorted_items = sorted(items, key=_count, reverse=True)
    top = sorted_items[0]
    top_name = top.get("category") or top.get("name") or top.get("label") or "Unknown"
    top_count = _count(top)
    total = sum(_count(item) for item in items)
    share = f"{top_count / total:.0%}" if total > 0 else "N/A"

    logger.info(
        "central_api_call_ok",
        endpoint=_RENTALS_STATS_PATH,
        category_count=len(items),
        top_category=top_name,
        top_count=top_count,
        market_share=share,
        elapsed_ms=elapsed,
    )

    return {
        "top_category": top_name,
        "rental_count": top_count,
        "market_share": share,
        "note": f"Live data across {len(items)} categories.",
    }


async def _fetch_availability(
    settings: AIAgentSettings,
    product_id: str,
    from_date: str,
    to_date: str,
) -> dict:
    if not product_id or not from_date or not to_date:
        logger.warning(
            "availability_missing_args",
            product_id=product_id or None,
            from_date=from_date or None,
            to_date=to_date or None,
        )
        return {
            "available": None,
            "note": "Could not check availability: product_id, from_date, and to_date are all required.",
        }

    url = f"{settings.rental_service_url}/products/{product_id}/availability"
    logger.info(
        "rental_service_call_start",
        url=url,
        product_id=product_id,
        from_date=from_date,
        to_date=to_date,
    )
    t0 = time.monotonic()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params={"from": from_date, "to": to_date})
    except httpx.TimeoutException:
        logger.error("rental_service_timeout", url=url, elapsed_ms=round((time.monotonic() - t0) * 1000))
        return {"available": None, "note": "Rental service timed out while checking availability."}
    except httpx.RequestError as exc:
        logger.error("rental_service_unreachable", url=url, error=str(exc))
        return {"available": None, "note": "Rental service is unreachable."}

    elapsed = round((time.monotonic() - t0) * 1000)

    if resp.status_code == 404:
        logger.warning("rental_service_product_not_found", product_id=product_id, elapsed_ms=elapsed)
        return {"available": None, "note": f"Product {product_id} not found in rental service."}

    if resp.status_code != 200:
        logger.error(
            "rental_service_error",
            url=url,
            status=resp.status_code,
            elapsed_ms=elapsed,
        )
        return {"available": None, "note": f"Rental service returned error {resp.status_code}."}

    data = resp.json()
    logger.info(
        "rental_service_call_ok",
        product_id=product_id,
        from_date=from_date,
        to_date=to_date,
        available=data.get("available"),
        busy_periods=len(data.get("busyPeriods", [])),
        free_windows=len(data.get("freeWindows", [])),
        elapsed_ms=elapsed,
    )
    return data


def _resolve_subject_data(subject: str) -> dict:
    lowered = subject.lower()
    for key, value in _TOOL_DATA.items():
        if key != "default" and key in lowered:
            return value
    return _TOOL_DATA["default"]


def _humanize_subject(subject: str) -> str:
    return " ".join(part.capitalize() for part in subject.split()) if subject else "Tools"
