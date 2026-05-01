import json
import re
import time
from dataclasses import dataclass
from datetime import date, timedelta

import asyncio

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
        description="Returns the peak rental period within a month range. Requires from_month and to_month in YYYY-MM format.",
        arguments=("from_month", "to_month"),
    ),
    ToolSpec(
        name="get_surge_days",
        description="Returns rental surge days for a specific month. Requires month in YYYY-MM format.",
        arguments=("month",),
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
    normalized = {key: str(value).strip() for key, value in arguments.items() if value is not None and str(value).strip()}
    subject = normalized.get("category") or normalized.get("subject") or normalized.get("region") or ""

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
        result = await _fetch_recommendations(settings, subject)
    elif name == "get_peak_window":
        from_month = normalized.get("from_month", "")
        to_month = normalized.get("to_month", "")
        result = await _fetch_peak_window(settings, from_month, to_month)
    elif name == "get_surge_days":
        month = normalized.get("month", "")
        result = await _fetch_surge_days(settings, month)
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
    logger.info("grpc_call_start", service="analytics", method="GetTrends")
    t0 = time.monotonic()
    try:
        payload = await _call_analytics_json(
            settings,
            analytics_pb2.TrendsRequest(category=""),
            "GetTrends",
        )
    except RuntimeError as exc:
        logger.error("grpc_call_failed", service="analytics", method="GetTrends", error=str(exc), elapsed_ms=round((time.monotonic() - t0) * 1000))
        return {"top_category": "Unavailable", "rental_count": None, "market_share": "N/A", "note": str(exc)}

    counts = payload.get("by_category", {})
    if not isinstance(counts, dict) or not counts:
        logger.warning("grpc_empty_response", service="analytics", method="GetTrends")
        return {"top_category": "Unknown", "rental_count": None, "market_share": "N/A", "note": "Analytics service returned no category trends."}

    sorted_items = sorted(
        ((str(cat), int(cnt)) for cat, cnt in counts.items()),
        key=lambda item: (-item[1], item[0]),
    )
    total = sum(cnt for _cat, cnt in sorted_items)
    top_name, top_count = sorted_items[0]
    share = f"{top_count / total:.0%}" if total > 0 else "N/A"
    logger.info("grpc_call_ok", service="analytics", method="GetTrends", top_category=top_name, elapsed_ms=round((time.monotonic() - t0) * 1000))
    return {
        "top_category": _humanize_subject(top_name),
        "rental_count": top_count,
        "market_share": share,
        "note": f"Live data across {len(sorted_items)} categories via gRPC.",
    }


async def _fetch_availability(
    settings: AIAgentSettings,
    product_id: str,
    from_date: str,
    to_date: str,
) -> dict:
    if not product_id or not from_date or not to_date:
        logger.warning("availability_missing_args", product_id=product_id or None, from_date=from_date or None, to_date=to_date or None)
        return {"available": None, "note": "Could not check availability: product_id, from_date, and to_date are all required."}

    logger.info("grpc_call_start", service="rental", method="GetAvailability", product_id=product_id, from_date=from_date, to_date=to_date)
    t0 = time.monotonic()
    try:
        response = await _call_rental_availability(
            settings,
            rental_pb2.AvailabilityRequest(
                product_id=int(product_id),
                from_date=from_date,
                to_date=to_date,
            ),
        )
    except RuntimeError as exc:
        logger.error("grpc_call_failed", service="rental", method="GetAvailability", error=str(exc), elapsed_ms=round((time.monotonic() - t0) * 1000))
        return {"available": None, "note": str(exc)}

    availability = "Available" if response.available else "Not available in the requested period"
    if response.available:
        restock_eta = "Available immediately."
    elif response.free_windows:
        restock_eta = f"Next free window starts {response.free_windows[0].start}."
    else:
        restock_eta = "No free window found in the requested range."
    logger.info("grpc_call_ok", service="rental", method="GetAvailability", available=response.available, elapsed_ms=round((time.monotonic() - t0) * 1000))
    return {
        "productId": int(product_id),
        "from": from_date,
        "to": to_date,
        "available": response.available,
        "availability": availability,
        "restock_eta": restock_eta,
        "busyPeriods": [{"start": p.start, "end": p.end} for p in response.busy_periods],
        "freeWindows": [{"start": w.start, "end": w.end} for w in response.free_windows],
    }


async def _fetch_recommendations(settings: AIAgentSettings, subject: str) -> dict:
    logger.info("grpc_call_start", service="analytics", method="GetRecommendations", category=subject or None)
    t0 = time.monotonic()
    try:
        async with asyncio.timeout(30.0):
            payload = await _call_analytics_json(
                settings,
                analytics_pb2.RecommendationsRequest(category=subject, date=date.today().isoformat(), limit=3),
                "GetRecommendations",
            )
    except (RuntimeError, TimeoutError) as exc:
        logger.error("grpc_call_failed", service="analytics", method="GetRecommendations", error=str(exc), elapsed_ms=round((time.monotonic() - t0) * 1000))
        return {"category": _humanize_subject(subject or "tools"), "recommendations": [], "note": str(exc)}

    recommendations = payload.get("recommendations", [])
    if not isinstance(recommendations, list):
        recommendations = []

    filtered = [item for item in recommendations if not subject or str(item.get("category", "")).lower() == subject.lower()]
    selected = filtered or recommendations
    names = [str(item.get("name", "Unknown")) for item in selected[:3]]
    category_label = subject or (str(selected[0].get("category", "")) if selected else "tools")
    note = "Live data via analytics-service gRPC."
    if subject and not filtered:
        note = "Live data via analytics-service gRPC; no exact category match returned."

    logger.info("grpc_call_ok", service="analytics", method="GetRecommendations", result_count=len(names), elapsed_ms=round((time.monotonic() - t0) * 1000))
    return {
        "category": _humanize_subject(category_label),
        "recommendations": names or ["No recommendations available right now"],
        "note": note,
    }


async def _fetch_peak_window(settings: AIAgentSettings, from_month: str, to_month: str) -> dict:
    if not from_month or not to_month:
        logger.warning("peak_window_missing_args", from_month=from_month or None, to_month=to_month or None)
        return {"peakWindow": None, "note": "Could not fetch peak window: from_month and to_month are required (YYYY-MM)."}

    logger.info("grpc_call_start", service="analytics", method="GetPeakWindow", from_month=from_month, to_month=to_month)
    t0 = time.monotonic()
    try:
        payload = await _call_analytics_json(
            settings,
            analytics_pb2.PeakWindowRequest(from_month=from_month, to_month=to_month),
            "GetPeakWindow",
        )
    except RuntimeError as exc:
        logger.error("grpc_call_failed", service="analytics", method="GetPeakWindow", error=str(exc), elapsed_ms=round((time.monotonic() - t0) * 1000))
        return {"peakWindow": None, "note": str(exc)}

    peak_window = payload.get("peakWindow", {})
    if not isinstance(peak_window, dict):
        peak_window = {}

    logger.info("grpc_call_ok", service="analytics", method="GetPeakWindow", peak_start=peak_window.get("start"), elapsed_ms=round((time.monotonic() - t0) * 1000))
    return payload


async def _fetch_surge_days(settings: AIAgentSettings, month: str) -> dict:
    if not month:
        logger.warning("surge_days_missing_args", month=None)
        return {"surgeDays": None, "note": "Could not fetch surge days: month is required (YYYY-MM)."}

    logger.info("grpc_call_start", service="analytics", method="GetSurgeDays", month=month)
    t0 = time.monotonic()
    try:
        payload = await _call_analytics_json(
            settings,
            analytics_pb2.SurgeDaysRequest(month=month),
            "GetSurgeDays",
        )
    except RuntimeError as exc:
        logger.error("grpc_call_failed", service="analytics", method="GetSurgeDays", error=str(exc), elapsed_ms=round((time.monotonic() - t0) * 1000))
        return {"surgeDays": None, "note": str(exc)}

    logger.info("grpc_call_ok", service="analytics", method="GetSurgeDays", month=month, elapsed_ms=round((time.monotonic() - t0) * 1000))
    return payload


async def _call_analytics_json(
    settings: AIAgentSettings,
    request: object,
    method_name: str,
) -> dict:
    async with asyncio.timeout(10.0):
        async with grpc.aio.insecure_channel(settings.analytics_service_addr) as channel:
            stub = analytics_pb2_grpc.AnalyticsServiceStub(channel)
            method = getattr(stub, method_name)
            try:
                response = await method(request)
            except grpc.RpcError as exc:
                raise RuntimeError(_grpc_error_message("analytics-service", exc)) from exc
    return _parse_json_payload(response.json_data)


async def _call_rental_json(
    settings: AIAgentSettings,
    request: object,
    method_name: str,
) -> dict:
    async with asyncio.timeout(10.0):
        async with grpc.aio.insecure_channel(settings.rental_service_addr) as channel:
            stub = rental_pb2_grpc.RentalServiceStub(channel)
            method = getattr(stub, method_name)
            try:
                response = await method(request)
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
