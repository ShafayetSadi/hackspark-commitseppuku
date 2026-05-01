import json
import re
import time
from dataclasses import dataclass
from datetime import date, timedelta

import grpc
import grpc.aio
from ai_agent_service.core.config import AIAgentSettings

from shared.app_core.logging import get_logger
from shared.grpc_gen import analytics_pb2, analytics_pb2_grpc, rental_pb2, rental_pb2_grpc

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
        description="Returns inventory availability for a product or category.",
        arguments=("subject",),
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
    subject = (
        normalized.get("category") or normalized.get("subject") or normalized.get("region") or ""
    )

    logger.debug("tool_dispatch", tool=name, arguments=normalized, subject=subject or None)

    t0 = time.monotonic()
    if name == "get_top_category":
        result = await _fetch_top_category(settings)
    elif name == "get_availability":
        result = await _fetch_availability(settings, subject)
    elif name == "get_recommendations":
        result = await _fetch_recommendations(settings, subject)
    elif name == "get_peak_window":
        result = await _fetch_peak_window(settings, subject)
    elif name == "get_surge_days":
        result = await _fetch_surge_days(settings, subject)
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
    payload = await _call_analytics_json(
        settings,
        analytics_pb2.TrendsRequest(category=""),
        "GetTrends",
    )
    counts = payload.get("by_category", {})
    if not isinstance(counts, dict) or not counts:
        return {
            "top_category": "Unknown",
            "rental_count": None,
            "market_share": "N/A",
            "note": "Analytics service returned no category trends.",
        }

    sorted_items = sorted(
        ((str(category), int(count)) for category, count in counts.items()),
        key=lambda item: (-item[1], item[0]),
    )
    total = sum(count for _category, count in sorted_items)
    if total <= 0:
        return {
            "top_category": "Unknown",
            "rental_count": None,
            "market_share": "N/A",
            "note": "Analytics service returned empty category volumes.",
        }

    top_name, top_count = sorted_items[0]
    share = f"{top_count / total:.0%}" if total > 0 else "N/A"
    return {
        "top_category": _humanize_subject(top_name),
        "rental_count": top_count,
        "market_share": share,
        "note": f"Computed from live analytics across {len(sorted_items)} categories via gRPC.",
    }


async def _fetch_recommendations(settings: AIAgentSettings, subject: str) -> dict:
    today = date.today().isoformat()
    payload = await _call_analytics_json(
        settings,
        analytics_pb2.RecommendationsRequest(category=subject, date=today, limit=3),
        "GetRecommendations",
        timeout=30.0,
    )
    recommendations = payload.get("recommendations", [])
    if not isinstance(recommendations, list):
        recommendations = []

    filtered = [
        item
        for item in recommendations
        if not subject or str(item.get("category", "")).lower() == subject.lower()
    ]
    selected = filtered or recommendations
    names = [str(item.get("name", "Unknown")) for item in selected[:3]]
    category_label = subject or (str(selected[0].get("category", "")) if selected else "tools")
    note = "Grounded via analytics-service gRPC seasonal recommendation data."
    if subject and not filtered:
        note = (
            "Grounded via analytics-service gRPC seasonal recommendation data; "
            "no exact category match was returned."
        )

    return {
        "category": _humanize_subject(category_label),
        "recommendations": names or ["No recommendations available right now"],
        "note": note,
    }


async def _fetch_peak_window(settings: AIAgentSettings, subject: str) -> dict:
    current_month = date.today().strftime("%Y-%m")
    payload = await _call_analytics_json(
        settings,
        analytics_pb2.PeakWindowRequest(from_month=current_month, to_month=current_month),
        "GetPeakWindow",
    )
    peak_window = payload.get("peakWindow", {})
    if not isinstance(peak_window, dict):
        peak_window = {}

    start = str(peak_window.get("from", "unknown"))
    end = str(peak_window.get("to", "unknown"))
    total_rentals = peak_window.get("totalRentals", 0)
    return {
        "category": _humanize_subject(subject or "inventory"),
        "peak_window": f"{start} to {end}",
        "note": (
            f"Grounded via analytics-service gRPC with {total_rentals} rentals in the peak window."
        ),
    }


async def _fetch_surge_days(settings: AIAgentSettings, subject: str) -> dict:
    current_month = date.today().strftime("%Y-%m")
    payload = await _call_analytics_json(
        settings,
        analytics_pb2.SurgeDaysRequest(month=current_month),
        "GetSurgeDays",
    )
    rows = payload.get("data", [])
    if not isinstance(rows, list):
        rows = []

    ranked_days = sorted(
        ((str(row.get("date", "")), int(row.get("count", 0))) for row in rows if row.get("date")),
        key=lambda item: (-item[1], item[0]),
    )
    top_dates = [day for day, count in ranked_days if count > 0][:2]
    surge_days = " and ".join(top_dates) if top_dates else "no surge days detected"

    return {
        "category": _humanize_subject(subject or "inventory"),
        "surge_days": surge_days,
        "note": "Grounded via analytics-service gRPC demand-spike data.",
    }


async def _fetch_availability(settings: AIAgentSettings, subject: str) -> dict:
    product_id = _extract_product_id(subject)
    product_name = None

    if product_id is None:
        category = _normalize_subject(subject)
        payload = await _call_rental_json(
            settings,
            rental_pb2.ProductsQuery(category=category, limit="1"),
            "ListProducts",
        )
        items = payload.get("data", [])
        if not isinstance(items, list) or not items:
            return {
                "subject": _humanize_subject(subject or "inventory"),
                "availability": "Unavailable",
                "restock_eta": "No matching product found from rental-service.",
            }

        first_product = items[0]
        product_id = int(first_product.get("id", 0))
        product_name = str(first_product.get("name", f"Product #{product_id}"))
    else:
        product_name = f"Product #{product_id}"

    today = date.today()
    response = await _call_rental_availability(
        settings,
        rental_pb2.AvailabilityRequest(
            product_id=product_id,
            from_date=today.isoformat(),
            to_date=(today + timedelta(days=14)).isoformat(),
        ),
    )
    availability = "Available" if response.available else "Booked in the next 14 days"
    restock_eta = (
        "Available immediately."
        if response.available
        else (
            f"Next free window starts {response.free_windows[0].start}."
            if response.free_windows
            else "No free window found in the next 14 days."
        )
    )
    return {
        "subject": product_name,
        "availability": availability,
        "restock_eta": restock_eta,
    }


async def _call_analytics_json(
    settings: AIAgentSettings,
    request: object,
    method_name: str,
    *,
    timeout: float | None = None,
) -> dict:
    async with grpc.aio.insecure_channel(settings.analytics_service_addr) as channel:
        stub = analytics_pb2_grpc.AnalyticsServiceStub(channel)
        method = getattr(stub, method_name)
        try:
            response = await method(request, timeout=timeout)
        except grpc.RpcError as exc:
            raise RuntimeError(_grpc_error_message("analytics-service", exc)) from exc
    return _parse_json_payload(response.json_data)


async def _call_rental_json(
    settings: AIAgentSettings,
    request: object,
    method_name: str,
    *,
    timeout: float | None = None,
) -> dict:
    async with grpc.aio.insecure_channel(settings.rental_service_addr) as channel:
        stub = rental_pb2_grpc.RentalServiceStub(channel)
        method = getattr(stub, method_name)
        try:
            response = await method(request, timeout=timeout)
        except grpc.RpcError as exc:
            raise RuntimeError(_grpc_error_message("rental-service", exc)) from exc
    return _parse_json_payload(response.json_data)


async def _call_rental_availability(
    settings: AIAgentSettings,
    request: rental_pb2.AvailabilityRequest,
) -> rental_pb2.AvailabilityResponse:
    async with grpc.aio.insecure_channel(settings.rental_service_addr) as channel:
        stub = rental_pb2_grpc.RentalServiceStub(channel)
        try:
            return await stub.GetAvailability(request)
        except grpc.RpcError as exc:
            raise RuntimeError(_grpc_error_message("rental-service", exc)) from exc


def _parse_json_payload(json_data: str) -> dict:
    payload = json.loads(json_data)
    return payload if isinstance(payload, dict) else {"data": payload}


def _grpc_error_message(service_name: str, exc: grpc.RpcError) -> str:
    code = exc.code()  # type: ignore[union-attr]
    details = exc.details() or (code.name if code is not None else "UNKNOWN")  # type: ignore[union-attr]
    return f"{service_name} gRPC call failed: {details}"


def _extract_product_id(subject: str) -> int | None:
    match = re.search(r"\d+", subject)
    if match is None:
        return None
    return int(match.group(0))


def _normalize_subject(subject: str) -> str:
    return subject.strip().lower() or "tools"


def _humanize_subject(subject: str) -> str:
    return " ".join(part.capitalize() for part in subject.split()) if subject else "Tools"
