from __future__ import annotations

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


def test_list_products_invalid_category_returns_helpful_400(rental_runtime, monkeypatch):
    async def fake_categories(_client):
        return type(
            "Snapshot", (), {"ordered": ["TOOLS", "OUTDOOR"], "values": {"TOOLS", "OUTDOOR"}}
        )()

    monkeypatch.setattr(rental_runtime.rental_logic, "get_categories_cached", fake_categories)
    client = FakeCentralClient({"/api/data/products": {"data": []}})

    try:
        import asyncio

        asyncio.run(
            rental_runtime.rental_logic.list_products(
                client,
                category="INVALID",
                page="1",
                limit="20",
            )
        )
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == {
            "error": "Invalid category 'INVALID'",
            "validCategories": ["TOOLS", "OUTDOOR"],
        }
    else:
        raise AssertionError("Expected HTTPException")


def test_product_availability_merges_busy_periods_and_finds_free_windows(rental_runtime):
    client = FakeCentralClient(
        {
            "/api/data/rentals": {
                "data": [
                    {
                        "rentalStart": "2024-02-28T00:00:00.000Z",
                        "rentalEnd": "2024-03-02T00:00:00.000Z",
                    },
                    {
                        "rentalStart": "2024-03-02T00:00:00.000Z",
                        "rentalEnd": "2024-03-05T00:00:00.000Z",
                    },
                    {
                        "rentalStart": "2024-03-09T00:00:00.000Z",
                        "rentalEnd": "2024-03-16T00:00:00.000Z",
                    },
                ],
                "page": 1,
                "limit": 100,
                "totalPages": 1,
            }
        }
    )

    import asyncio

    result = asyncio.run(
        rental_runtime.rental_logic.get_product_availability(
            client,
            product_id=42,
            from_date="2024-03-01",
            to_date="2024-03-14",
        )
    )

    assert result == {
        "productId": 42,
        "from": "2024-03-01",
        "to": "2024-03-14",
        "available": False,
        "busyPeriods": [
            {"start": "2024-02-28", "end": "2024-03-05"},
            {"start": "2024-03-09", "end": "2024-03-16"},
        ],
        "freeWindows": [{"start": "2024-03-06", "end": "2024-03-08"}],
    }


def test_kth_busiest_date_uses_earlier_date_for_ties(rental_runtime):
    client = FakeCentralClient(
        {
            "/api/data/rentals/stats": lambda params: {
                "data": [
                    {"date": f"{params['month']}-15T00:00:00.000Z", "count": 12},
                    {"date": f"{params['month']}-10T00:00:00.000Z", "count": 12},
                    {"date": f"{params['month']}-03T00:00:00.000Z", "count": 8},
                ]
            }
        }
    )

    import asyncio

    result = asyncio.run(
        rental_runtime.rental_logic.get_kth_busiest_date(
            client,
            from_month="2024-01",
            to_month="2024-01",
            k=2,
        )
    )

    assert result == {
        "from": "2024-01",
        "to": "2024-01",
        "k": 2,
        "date": "2024-01-15",
        "rentalCount": 12,
    }


def test_top_categories_uses_batch_product_fetches(rental_runtime):
    rentals = [
        {
            "productId": product_id,
            "renterId": 101,
            "rentalStart": "2024-01-01T00:00:00.000Z",
            "rentalEnd": "2024-01-02T00:00:00.000Z",
        }
        for product_id in range(1, 56)
    ]
    batch_calls: list[str] = []

    def rentals_handler(_params):
        return {"data": rentals, "page": 1, "limit": 100, "totalPages": 1}

    def batch_handler(params):
        batch_calls.append(params["ids"])
        ids = [int(item) for item in params["ids"].split(",")]
        return {
            "data": [
                {
                    "id": product_id,
                    "category": "ELECTRONICS" if product_id <= 30 else "TOOLS",
                }
                for product_id in ids
            ],
            "missing": [],
        }

    client = FakeCentralClient(
        {
            "/api/data/rentals": rentals_handler,
            "/api/data/products/batch": batch_handler,
        }
    )

    import asyncio

    result = asyncio.run(
        rental_runtime.rental_logic.get_user_top_categories(client, user_id=101, k=2)
    )

    assert len(batch_calls) == 2
    assert result == {
        "userId": 101,
        "topCategories": [
            {"category": "ELECTRONICS", "rentalCount": 30},
            {"category": "TOOLS", "rentalCount": 25},
        ],
    }


def test_longest_free_streak_clips_to_year_bounds(rental_runtime):
    client = FakeCentralClient(
        {
            "/api/data/rentals": {
                "data": [
                    {
                        "rentalStart": "2022-12-20T00:00:00.000Z",
                        "rentalEnd": "2023-01-10T00:00:00.000Z",
                    },
                    {
                        "rentalStart": "2023-03-01T00:00:00.000Z",
                        "rentalEnd": "2023-03-05T00:00:00.000Z",
                    },
                    {
                        "rentalStart": "2023-07-01T00:00:00.000Z",
                        "rentalEnd": "2024-01-05T00:00:00.000Z",
                    },
                ],
                "page": 1,
                "limit": 100,
                "totalPages": 1,
            }
        }
    )

    import asyncio

    result = asyncio.run(
        rental_runtime.rental_logic.get_longest_free_streak(client, product_id=77, year=2023)
    )

    assert result == {
        "productId": 77,
        "year": 2023,
        "longestFreeStreak": {
            "from": "2023-03-06",
            "to": "2023-06-30",
            "days": 117,
        },
    }
