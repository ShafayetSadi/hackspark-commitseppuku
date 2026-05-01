import pytest


class FakeCentralClient:
    def __init__(self, payload):
        self.payload = payload

    async def get(self, path: str, params=None):
        assert params is None
        assert path == "/api/data/users/42"
        return self.payload


@pytest.mark.asyncio
async def test_compute_discount_ranges(auth_runtime):
    compute_discount = auth_runtime.discount_service.compute_discount

    assert compute_discount(85) == 20
    assert compute_discount(60) == 15
    assert compute_discount(40) == 10
    assert compute_discount(20) == 5
    assert compute_discount(19) == 0


@pytest.mark.asyncio
async def test_get_user_discount(auth_runtime):
    result = await auth_runtime.discount_service.get_user_discount(
        FakeCentralClient({"securityScore": 78}),
        user_id=42,
    )

    assert result == {
        "userId": 42,
        "securityScore": 78,
        "discountPercent": 15,
    }
