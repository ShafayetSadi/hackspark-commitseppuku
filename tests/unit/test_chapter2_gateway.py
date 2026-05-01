import grpc
import pytest
from fastapi import Request
from fastapi.responses import JSONResponse


class FakeRpcError(grpc.RpcError):
    def __init__(self, status_code: grpc.StatusCode, detail):
        self._status_code = status_code
        self._detail = detail

    def code(self):
        return self._status_code

    def details(self):
        return self._detail


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


@pytest.mark.asyncio
async def test_gateway_discount_route_maps_grpc_response(gateway_runtime, monkeypatch):
    class Stub:
        async def GetDiscount(self, request):
            assert request.user_id == 42
            return gateway_runtime.api_routes.user_pb2.DiscountResponse(
                user_id=42,
                security_score=85,
                discount_percent=20,
            )

    monkeypatch.setattr(gateway_runtime.api_routes.user_client, "get_stub", lambda _addr: Stub())

    settings = gateway_runtime.core_config.get_settings()
    response = await gateway_runtime.api_routes.discount(42, settings=settings)
    assert response == {"userId": 42, "securityScore": 85, "discountPercent": 20}


@pytest.mark.asyncio
async def test_gateway_availability_route_maps_request_and_response(gateway_runtime, monkeypatch):
    class Stub:
        async def GetAvailability(self, request):
            assert request.product_id == 42
            assert request.from_date == "2024-03-01"
            assert request.to_date == "2024-03-14"
            return gateway_runtime.api_routes.rental_pb2.AvailabilityResponse(
                product_id=42,
                from_date="2024-03-01",
                to_date="2024-03-14",
                available=False,
                busy_periods=[
                    gateway_runtime.api_routes.rental_pb2.DateRange(
                        start="2024-02-28",
                        end="2024-03-05",
                    )
                ],
                free_windows=[
                    gateway_runtime.api_routes.rental_pb2.DateRange(
                        start="2024-03-06",
                        end="2024-03-08",
                    )
                ],
            )

    monkeypatch.setattr(gateway_runtime.api_routes.rental_client, "get_stub", lambda _addr: Stub())

    settings = gateway_runtime.core_config.get_settings()
    response = await gateway_runtime.api_routes.get_product_availability(
        42,
        from_date="2024-03-01",
        to_date="2024-03-14",
        settings=settings,
    )
    assert response == {
        "productId": 42,
        "from": "2024-03-01",
        "to": "2024-03-14",
        "available": False,
        "busyPeriods": [{"start": "2024-02-28", "end": "2024-03-05"}],
        "freeWindows": [{"start": "2024-03-06", "end": "2024-03-08"}],
    }


@pytest.mark.asyncio
async def test_gateway_invalid_category_error_preserves_structured_detail(
    gateway_runtime, monkeypatch
):
    class Stub:
        async def ListProducts(self, _request):
            raise FakeRpcError(
                grpc.StatusCode.INVALID_ARGUMENT,
                '{"error":"Invalid category \'BAD\'","validCategories":["TOOLS","OUTDOOR"]}',
            )

    monkeypatch.setattr(gateway_runtime.api_routes.rental_client, "get_stub", lambda _addr: Stub())

    settings = gateway_runtime.core_config.get_settings()
    response = await gateway_runtime.api_routes.list_products(
        build_request("/rentals/products", "category=BAD"),
        settings=settings,
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert response.body == (
        b'{"error":"Invalid category \'BAD\'","validCategories":["TOOLS","OUTDOOR"]}'
    )


@pytest.mark.asyncio
async def test_gateway_products_route_forwards_extra_query_params(gateway_runtime, monkeypatch):
    class Stub:
        async def ListProducts(self, request):
            assert request.category == "TOOLS"
            assert request.page == "2"
            assert request.limit == "20"
            assert dict(request.extra_params) == {"owner_id": "7", "sort": "price_desc"}
            return gateway_runtime.api_routes.rental_pb2.ProductsResponse(
                json_data='{"data":[],"page":2,"limit":20,"total":0,"totalPages":0}'
            )

    monkeypatch.setattr(gateway_runtime.api_routes.rental_client, "get_stub", lambda _addr: Stub())

    settings = gateway_runtime.core_config.get_settings()
    response = await gateway_runtime.api_routes.list_products(
        build_request(
            "/rentals/products",
            "category=TOOLS&page=2&limit=20&owner_id=7&sort=price_desc",
        ),
        settings=settings,
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
