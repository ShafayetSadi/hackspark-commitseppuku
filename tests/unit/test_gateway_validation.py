import pytest
from pydantic import ValidationError


def test_register_body_rejects_short_password(gateway_runtime):
    with pytest.raises(ValidationError) as exc_info:
        gateway_runtime.api_routes.RegisterBody(
            email="sadi@gmail.com",
            password="123456",
            name="sadi",
        )

    assert "at least 8 characters" in str(exc_info.value)
