from __future__ import annotations

from fastapi import Request


def build_request(path: str, query_string: str = "") -> Request:
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "query_string": query_string.encode(),
        "state": {},
        "headers": [],
    }
    return Request(scope, receive=receive)


async def test_gateway_peak_window_route_maps_grpc_response(gateway_runtime, monkeypatch):
    class Stub:
        async def GetPeakWindow(self, request):
            assert request.from_month == "2024-01"
            assert request.to_month == "2024-06"
            return gateway_runtime.api_routes.analytics_pb2.AnalyticsResponse(
                json_data=(
                    '{"from":"2024-01","to":"2024-06","peakWindow":'
                    '{"from":"2024-03-10","to":"2024-03-16","totalRentals":2847}}'
                )
            )

    monkeypatch.setattr(
        gateway_runtime.api_routes.analytics_client, "get_stub", lambda _addr: Stub()
    )

    settings = gateway_runtime.core_config.get_settings()
    response = await gateway_runtime.api_routes.get_peak_window(
        build_request("/analytics/peak-window", "from=2024-01&to=2024-06"),
        settings=settings,
    )

    assert response.body == (
        b'{"from":"2024-01","to":"2024-06","peakWindow":{"from":"2024-03-10",'
        b'"to":"2024-03-16","totalRentals":2847}}'
    )


async def test_gateway_surge_days_route_maps_grpc_response(gateway_runtime, monkeypatch):
    class Stub:
        async def GetSurgeDays(self, request):
            assert request.month == "2024-03"
            return gateway_runtime.api_routes.analytics_pb2.AnalyticsResponse(
                json_data=(
                    '{"month":"2024-03","data":['
                    '{"date":"2024-03-01","count":4,"nextSurgeDate":"2024-03-04","daysUntil":3},'
                    '{"date":"2024-03-31","count":3,"nextSurgeDate":null,"daysUntil":null}'
                    ']}'
                )
            )

    monkeypatch.setattr(
        gateway_runtime.api_routes.analytics_client, "get_stub", lambda _addr: Stub()
    )

    settings = gateway_runtime.core_config.get_settings()
    response = await gateway_runtime.api_routes.get_surge_days(
        build_request("/analytics/surge-days", "month=2024-03"),
        settings=settings,
    )

    assert response.body == (
        b'{"month":"2024-03","data":[{"date":"2024-03-01","count":4,'
        b'"nextSurgeDate":"2024-03-04","daysUntil":3},{"date":"2024-03-31",'
        b'"count":3,"nextSurgeDate":null,"daysUntil":null}]}'
    )


async def test_gateway_recommendations_route_maps_grpc_response(gateway_runtime, monkeypatch):
    class Stub:
        async def GetRecommendations(self, request, *, timeout=None):
            assert request.date == "2024-06-15"
            assert request.limit == 2
            assert timeout == 30.0
            return gateway_runtime.api_routes.analytics_pb2.AnalyticsResponse(
                json_data=(
                    '{"date":"2024-06-15","recommendations":['
                    '{"productId":1042,"name":"Elite Tent #1042","category":"OUTDOOR","score":24},'
                    '{"productId":88,"name":"Pro Kayak #88","category":"SPORTS","score":19}'
                    ']}'
                )
            )

    monkeypatch.setattr(
        gateway_runtime.api_routes.analytics_client, "get_stub", lambda _addr: Stub()
    )

    settings = gateway_runtime.core_config.get_settings()
    response = await gateway_runtime.api_routes.get_recommendations(
        build_request("/analytics/recommendations", "date=2024-06-15&limit=2"),
        settings=settings,
    )

    assert response.body == (
        b'{"date":"2024-06-15","recommendations":[{"productId":1042,'
        b'"name":"Elite Tent #1042","category":"OUTDOOR","score":24},'
        b'{"productId":88,"name":"Pro Kayak #88","category":"SPORTS","score":19}]}'
    )


async def test_gateway_recommendations_route_rejects_non_integer_limit(
    gateway_runtime, monkeypatch
):
    class Stub:
        async def GetRecommendations(self, _request):
            raise AssertionError("gateway should reject invalid limit before gRPC")

    monkeypatch.setattr(
        gateway_runtime.api_routes.analytics_client, "get_stub", lambda _addr: Stub()
    )

    settings = gateway_runtime.core_config.get_settings()

    try:
        await gateway_runtime.api_routes.get_recommendations(
            build_request("/analytics/recommendations", "date=2024-06-15&limit=abc"),
            settings=settings,
        )
    except gateway_runtime.api_routes.HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "Invalid limit"
    else:
        raise AssertionError("Expected HTTPException")


async def test_gateway_merged_feed_route_maps_grpc_response(gateway_runtime, monkeypatch):
    class Stub:
        async def GetMergedFeed(self, request):
            assert list(request.product_ids) == [12, 47, 88]
            assert request.limit == 3
            return gateway_runtime.api_routes.rental_pb2.MergedFeedResponse(
                product_ids=[12, 47, 88],
                limit=3,
                feed=[
                    gateway_runtime.api_routes.rental_pb2.FeedRental(
                        rental_id=5041,
                        product_id=88,
                        rental_start="2024-01-01",
                        rental_end="2024-01-05",
                    ),
                    gateway_runtime.api_routes.rental_pb2.FeedRental(
                        rental_id=12900,
                        product_id=12,
                        rental_start="2024-01-02",
                        rental_end="2024-01-09",
                    ),
                ],
            )

    monkeypatch.setattr(gateway_runtime.api_routes.rental_client, "get_stub", lambda _addr: Stub())

    settings = gateway_runtime.core_config.get_settings()
    response = await gateway_runtime.api_routes.merged_feed(
        build_request("/rentals/merged-feed", "productIds=12,47,88&limit=3"),
        settings=settings,
    )

    assert response == {
        "productIds": [12, 47, 88],
        "limit": 3,
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
        ],
    }


async def test_gateway_merged_feed_rejects_empty_product_id_segments(gateway_runtime, monkeypatch):
    class Stub:
        async def GetMergedFeed(self, _request):
            raise AssertionError("gateway should reject invalid productIds before gRPC")

    monkeypatch.setattr(gateway_runtime.api_routes.rental_client, "get_stub", lambda _addr: Stub())

    settings = gateway_runtime.core_config.get_settings()

    try:
        await gateway_runtime.api_routes.merged_feed(
            build_request("/rentals/merged-feed", "productIds=12,,88&limit=3"),
            settings=settings,
        )
    except gateway_runtime.api_routes.HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "productIds must be 1-10 comma-separated integers"
    else:
        raise AssertionError("Expected HTTPException")
