from dataclasses import dataclass


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
        description="Returns the strongest rental category and a few supporting stats.",
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


_TOOL_DATA = {
    "electronics": {
        "top_share": "31%",
        "availability": "84% in stock across flagship SKUs",
        "peak_window": "Friday 4pm-8pm",
        "surge_days": "Tuesday and Friday",
        "recommendations": ["Mirrorless cameras", "Portable projectors", "Drone kits"],
    },
    "outdoor": {
        "top_share": "23%",
        "availability": "76% in stock with weekend pressure",
        "peak_window": "Saturday 8am-noon",
        "surge_days": "Thursday and Saturday",
        "recommendations": ["Camping tents", "Trail GPS units", "Cooler bundles"],
    },
    "tools": {
        "top_share": "28%",
        "availability": "68% in stock with high contractor demand",
        "peak_window": "Monday 7am-10am",
        "surge_days": "Monday and Wednesday",
        "recommendations": ["Rotary hammer drills", "Pressure washers", "Tile saws"],
    },
    "default": {
        "top_share": "19%",
        "availability": "73% in stock overall",
        "peak_window": "Weekdays 10am-1pm",
        "surge_days": "Wednesday and Friday",
        "recommendations": ["Power tool bundles", "Generator rentals", "Lighting kits"],
    },
}


def describe_tools() -> list[dict]:
    return [
        {
            "name": spec.name,
            "description": spec.description,
            "arguments": list(spec.arguments),
        }
        for spec in TOOL_SPECS
    ]


def execute_tool(name: str, arguments: dict[str, str]) -> ToolExecution:
    normalized = {key: value.strip() for key, value in arguments.items() if value and value.strip()}
    subject = normalized.get("category") or normalized.get("subject") or normalized.get("region") or ""
    data = _resolve_subject_data(subject)

    if name == "get_top_category":
        result = {
            "top_category": _humanize_subject(subject or "tools"),
            "market_share": data["top_share"],
            "note": "Demand remains strongest in contractor and weekend-prep segments.",
        }
    elif name == "get_availability":
        result = {
            "subject": _humanize_subject(subject or "inventory"),
            "availability": data["availability"],
            "restock_eta": "12-24 hours for depleted items",
        }
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
        raise ValueError(f"Unknown tool: {name}")

    return ToolExecution(name=name, arguments=normalized, result=result)


def _resolve_subject_data(subject: str) -> dict:
    lowered = subject.lower()
    for key, value in _TOOL_DATA.items():
        if key != "default" and key in lowered:
            return value
    return _TOOL_DATA["default"]


def _humanize_subject(subject: str) -> str:
    return " ".join(part.capitalize() for part in subject.split()) if subject else "Tools"
