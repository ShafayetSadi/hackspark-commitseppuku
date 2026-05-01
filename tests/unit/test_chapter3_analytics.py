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


def test_surge_days_fills_missing_days_and_finds_next_higher_day(analytics_runtime):
    def stats_handler(params):
        assert params == {"group_by": "date", "month": "2024-03"}
        return {
            "data": [
                {"date": "2024-03-01T00:00:00.000Z", "count": 4},
                {"date": "2024-03-03T00:00:00.000Z", "count": 2},
                {"date": "2024-03-04T00:00:00.000Z", "count": 7},
                {"date": "2024-03-06T00:00:00.000Z", "count": 7},
                {"date": "2024-03-31T00:00:00.000Z", "count": 3},
            ]
        }

    client = FakeCentralClient({"/api/data/rentals/stats": stats_handler})

    result = asyncio.run(
        analytics_runtime.analytics_logic.compute_surge_days(
            client,
            month="2024-03",
        )
    )

    assert client.calls == [("/api/data/rentals/stats", {"group_by": "date", "month": "2024-03"})]
    assert result["month"] == "2024-03"
    assert len(result["data"]) == 31
    assert result["data"][:6] == [
        {
            "date": "2024-03-01",
            "count": 4,
            "nextSurgeDate": "2024-03-04",
            "daysUntil": 3,
        },
        {
            "date": "2024-03-02",
            "count": 0,
            "nextSurgeDate": "2024-03-03",
            "daysUntil": 1,
        },
        {
            "date": "2024-03-03",
            "count": 2,
            "nextSurgeDate": "2024-03-04",
            "daysUntil": 1,
        },
        {
            "date": "2024-03-04",
            "count": 7,
            "nextSurgeDate": None,
            "daysUntil": None,
        },
        {
            "date": "2024-03-05",
            "count": 0,
            "nextSurgeDate": "2024-03-06",
            "daysUntil": 1,
        },
        {
            "date": "2024-03-06",
            "count": 7,
            "nextSurgeDate": None,
            "daysUntil": None,
        },
    ]
    assert result["data"][-1] == {
        "date": "2024-03-31",
        "count": 3,
        "nextSurgeDate": None,
        "daysUntil": None,
    }


def test_surge_days_rejects_invalid_month_format(analytics_runtime):
    client = FakeCentralClient({"/api/data/rentals/stats": {"data": []}})

    try:
        asyncio.run(
            analytics_runtime.analytics_logic.compute_surge_days(
                client,
                month="2024-3",
            )
        )
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "Invalid month format; expected YYYY-MM"
    else:
        raise AssertionError("Expected HTTPException")


def test_recommendations_aggregate_two_historical_windows_and_enrich_products(analytics_runtime):
    def rentals_handler(params):
        if params["from"] == "2023-06-08" and params["to"] == "2023-06-22":
            return {
                "data": [
                    {"productId": 88, "rentalStart": "2023-06-10T00:00:00.000Z"},
                    {"productId": 88, "rentalStart": "2023-06-12T00:00:00.000Z"},
                    {"productId": 1042, "rentalStart": "2023-06-15T00:00:00.000Z"},
                    {"productId": 1042, "rentalStart": "2023-06-17T00:00:00.000Z"},
                    {"productId": 1042, "rentalStart": "2023-06-20T00:00:00.000Z"},
                ],
                "totalPages": 1,
            }
        if params["from"] == "2022-06-08" and params["to"] == "2022-06-22":
            return {
                "data": [
                    {"productId": 88, "rentalStart": "2022-06-09T00:00:00.000Z"},
                    {"productId": 88, "rentalStart": "2022-06-18T00:00:00.000Z"},
                    {"productId": 15, "rentalStart": "2022-06-18T00:00:00.000Z"},
                    {"productId": 15, "rentalStart": "2022-06-30T00:00:00.000Z"},
                ],
                "totalPages": 1,
            }
        raise AssertionError(f"unexpected rentals params: {params}")

    def products_handler(params):
        assert params == {"ids": "88,1042"}
        return {
            "data": [
                {"id": 88, "name": "Pro Kayak #88", "category": "SPORTS"},
                {"id": 1042, "name": "Elite Tent #1042", "category": "OUTDOOR"},
            ],
            "totalPages": 1,
        }

    client = FakeCentralClient(
        {
            "/api/data/rentals": rentals_handler,
            "/api/data/products/batch": products_handler,
        }
    )

    result = asyncio.run(
        analytics_runtime.analytics_logic.compute_recommendations(
            client,
            target_date="2024-06-15",
            limit=2,
        )
    )

    assert client.calls == [
        (
            "/api/data/rentals",
            {"from": "2023-06-08", "to": "2023-06-22", "limit": "100", "page": "1"},
        ),
        (
            "/api/data/rentals",
            {"from": "2022-06-08", "to": "2022-06-22", "limit": "100", "page": "1"},
        ),
        ("/api/data/products/batch", {"ids": "88,1042"}),
    ]
    assert result == {
        "date": "2024-06-15",
        "recommendations": [
            {
                "productId": 88,
                "name": "Pro Kayak #88",
                "category": "SPORTS",
                "score": 4,
            },
            {
                "productId": 1042,
                "name": "Elite Tent #1042",
                "category": "OUTDOOR",
                "score": 3,
            },
        ],
    }


def test_recommendations_support_year_boundary_windows(analytics_runtime):
    def rentals_handler(params):
        if params == {"from": "2022-12-27", "to": "2023-01-10", "limit": "100", "page": "1"}:
            return {"data": [], "totalPages": 1}
        if params == {"from": "2021-12-27", "to": "2022-01-10", "limit": "100", "page": "1"}:
            return {
                "data": [
                    {"productId": 5, "rentalStart": "2021-12-28T00:00:00.000Z"},
                    {"productId": 5, "rentalStart": "2022-01-04T00:00:00.000Z"},
                ],
                "totalPages": 1,
            }
        raise AssertionError(f"unexpected rentals params: {params}")

    def products_handler(params):
        assert params == {"ids": "5"}
        return {
            "data": [{"id": 5, "name": "Snow Tent #5", "category": "OUTDOOR"}],
            "totalPages": 1,
        }

    client = FakeCentralClient(
        {
            "/api/data/rentals": rentals_handler,
            "/api/data/products/batch": products_handler,
        }
    )

    result = asyncio.run(
        analytics_runtime.analytics_logic.compute_recommendations(
            client,
            target_date="2024-01-03",
            limit=1,
        )
    )

    assert result == {
        "date": "2024-01-03",
        "recommendations": [
            {
                "productId": 5,
                "name": "Snow Tent #5",
                "category": "OUTDOOR",
                "score": 2,
            }
        ],
    }


def test_recommendations_return_empty_when_no_historical_rentals_exist(analytics_runtime):
    def rentals_handler(params):
        return {"data": [], "totalPages": 1}

    client = FakeCentralClient({"/api/data/rentals": rentals_handler})

    result = asyncio.run(
        analytics_runtime.analytics_logic.compute_recommendations(
            client,
            target_date="2024-06-15",
            limit=5,
        )
    )

    assert result == {"date": "2024-06-15", "recommendations": []}


def test_recommendations_fail_fast_when_live_page_count_exceeds_safe_budget(analytics_runtime):
    def rentals_handler(params):
        assert params == {"from": "2023-06-08", "to": "2023-06-22", "limit": "100", "page": "1"}
        return {"data": [], "totalPages": 10}

    client = FakeCentralClient({"/api/data/rentals": rentals_handler})

    try:
        asyncio.run(
            analytics_runtime.analytics_logic.compute_recommendations(
                client,
                target_date="2024-06-15",
                limit=5,
            )
        )
    except HTTPException as exc:
        assert exc.status_code == 503
        assert exc.detail == (
            "Exact seasonal recommendations exceed the safe Central API page budget for live data"
        )
    else:
        raise AssertionError("Expected HTTPException")


def test_recommendations_reject_invalid_date_format(analytics_runtime):
    client = FakeCentralClient({"/api/data/rentals": {"data": []}})

    try:
        asyncio.run(
            analytics_runtime.analytics_logic.compute_recommendations(
                client,
                target_date="2024-6-15",
                limit=5,
            )
        )
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "Invalid date format; expected YYYY-MM-DD"
    else:
        raise AssertionError("Expected HTTPException")


def test_recommendations_reject_invalid_limit(analytics_runtime):
    client = FakeCentralClient({"/api/data/rentals": {"data": []}})

    try:
        asyncio.run(
            analytics_runtime.analytics_logic.compute_recommendations(
                client,
                target_date="2024-06-15",
                limit=0,
            )
        )
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "limit must be a positive integer <= 50"
    else:
        raise AssertionError("Expected HTTPException")
