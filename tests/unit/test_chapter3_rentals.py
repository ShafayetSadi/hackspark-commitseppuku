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


def test_parse_merged_feed_product_ids_validates_and_deduplicates(rental_runtime):
    assert rental_runtime.rental_logic.parse_merged_feed_product_ids("12,47,12,88") == [12, 47, 88]

    try:
        rental_runtime.rental_logic.parse_merged_feed_product_ids("12,,88")
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "productIds must be 1-10 comma-separated integers"
    else:
        raise AssertionError("Expected HTTPException")


def test_merged_feed_merges_sorted_streams_without_resorting(rental_runtime):
    payloads = {
        "12": {
            "data": [
                {
                    "id": 12900,
                    "productId": 12,
                    "rentalStart": "2024-01-02T00:00:00.000Z",
                    "rentalEnd": "2024-01-09T00:00:00.000Z",
                },
                {
                    "id": 12950,
                    "productId": 12,
                    "rentalStart": "2024-01-06T00:00:00.000Z",
                    "rentalEnd": "2024-01-10T00:00:00.000Z",
                },
            ],
            "page": 1,
            "limit": 100,
            "totalPages": 1,
        },
        "47": {
            "data": [
                {
                    "id": 3310,
                    "productId": 47,
                    "rentalStart": "2024-01-04T00:00:00.000Z",
                    "rentalEnd": "2024-01-07T00:00:00.000Z",
                }
            ],
            "page": 1,
            "limit": 100,
            "totalPages": 1,
        },
        "88": {
            "data": [
                {
                    "id": 5041,
                    "productId": 88,
                    "rentalStart": "2024-01-01T00:00:00.000Z",
                    "rentalEnd": "2024-01-05T00:00:00.000Z",
                },
                {
                    "id": 5042,
                    "productId": 88,
                    "rentalStart": "2024-01-03T00:00:00.000Z",
                    "rentalEnd": "2024-01-04T00:00:00.000Z",
                },
            ],
            "page": 1,
            "limit": 100,
            "totalPages": 1,
        },
    }

    def rentals_handler(params):
        return payloads[params["product_id"]]

    client = FakeCentralClient({"/api/data/rentals": rentals_handler})

    result = asyncio.run(
        rental_runtime.rental_logic.get_merged_feed(
            client,
            product_ids=[12, 47, 88, 12],
            limit=4,
        )
    )

    assert result == {
        "productIds": [12, 47, 88],
        "limit": 4,
        "feed": [
            {
                "rentalId": 5041,
                "productId": 88,
                "rentalStart": "2024-01-01",
                "rentalEnd": "2024-01-05",
            },
            {
                "rentalId": 12900,
                "productId": 12,
                "rentalStart": "2024-01-02",
                "rentalEnd": "2024-01-09",
            },
            {
                "rentalId": 5042,
                "productId": 88,
                "rentalStart": "2024-01-03",
                "rentalEnd": "2024-01-04",
            },
            {
                "rentalId": 3310,
                "productId": 47,
                "rentalStart": "2024-01-04",
                "rentalEnd": "2024-01-07",
            },
        ],
    }
    assert client.calls == [
        ("/api/data/rentals", {"product_id": "12", "limit": "100", "page": "1"}),
        ("/api/data/rentals", {"product_id": "47", "limit": "100", "page": "1"}),
        ("/api/data/rentals", {"product_id": "88", "limit": "100", "page": "1"}),
    ]


def test_merged_feed_rejects_invalid_limit(rental_runtime):
    client = FakeCentralClient({"/api/data/rentals": {"data": [], "page": 1, "totalPages": 1}})

    try:
        asyncio.run(
            rental_runtime.rental_logic.get_merged_feed(
                client,
                product_ids=[12],
                limit=101,
            )
        )
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "limit must be a positive integer <= 100"
    else:
        raise AssertionError("Expected HTTPException")
