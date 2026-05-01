from __future__ import annotations

import asyncio

from fastapi import HTTPException


class FakeCentralClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls: list[tuple[str, dict | None]] = []

    async def get(self, path: str, params: dict | None = None):
        normalized = dict(params or {})
        self.calls.append((path, normalized))
        handler = self.responses[path]
        if callable(handler):
            return handler(normalized)
        return handler


def test_peak_window_fills_missing_days_and_uses_running_window(analytics_runtime):
    counts_by_month = {
        "2024-01": {
            "2024-01-01": 2,
            "2024-01-03": 9,
            "2024-01-04": 1,
            "2024-01-05": 2,
            "2024-01-06": 2,
            "2024-01-07": 2,
            "2024-01-08": 2,
            "2024-01-09": 2,
        }
    }

    def stats_handler(params):
        month = params["month"]
        return {
            "data": [
                {"date": f"{day}T00:00:00.000Z", "count": count}
                for day, count in counts_by_month.get(month, {}).items()
            ]
        }

    client = FakeCentralClient({"/api/data/rentals/stats": stats_handler})

    result = asyncio.run(
        analytics_runtime.analytics_logic.compute_peak_window(
            client,
            from_month="2024-01",
            to_month="2024-01",
        )
    )

    assert client.calls == [("/api/data/rentals/stats", {"group_by": "date", "month": "2024-01"})]
    assert result == {
        "from": "2024-01",
        "to": "2024-01",
        "peakWindow": {
            "from": "2024-01-03",
            "to": "2024-01-09",
            "totalRentals": 20,
        },
    }


def test_peak_window_rejects_reversed_month_ranges(analytics_runtime):
    client = FakeCentralClient({"/api/data/rentals/stats": {"data": []}})

    try:
        asyncio.run(
            analytics_runtime.analytics_logic.compute_peak_window(
                client,
                from_month="2024-03",
                to_month="2024-02",
            )
        )
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "'from' must not be after 'to'"
    else:
        raise AssertionError("Expected HTTPException")


def test_peak_window_rejects_invalid_month_format(analytics_runtime):
    client = FakeCentralClient({"/api/data/rentals/stats": {"data": []}})

    try:
        asyncio.run(
            analytics_runtime.analytics_logic.compute_peak_window(
                client,
                from_month="2024-1",
                to_month="2024-02",
            )
        )
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "Invalid month format; expected YYYY-MM"
    else:
        raise AssertionError("Expected HTTPException")
