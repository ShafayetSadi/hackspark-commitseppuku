import pytest
from conftest import AsyncSessionAdapter
from fastapi import HTTPException, Request


@pytest.mark.anyio
async def test_register(auth_runtime):
    settings = auth_runtime.core_config.get_settings()
    payload = auth_runtime.schemas.RegisterRequest(
        email="team@example.com",
        password="password123",
        full_name="Hack Team",
    )

    with auth_runtime.session_factory() as sync_session:
        session = AsyncSessionAdapter(sync_session)
        response = await auth_runtime.api_routes.register(
            payload, session=session, settings=settings
        )

    assert response.token_type == "bearer"
    assert response.access_token


@pytest.mark.anyio
async def test_login(auth_runtime):
    settings = auth_runtime.core_config.get_settings()

    with auth_runtime.session_factory() as sync_session:
        session = AsyncSessionAdapter(sync_session)
        await auth_runtime.api_routes.register(
            auth_runtime.schemas.RegisterRequest(
                email="team@example.com",
                password="password123",
                full_name="Hack Team",
            ),
            session=session,
            settings=settings,
        )

    with auth_runtime.session_factory() as sync_session:
        session = AsyncSessionAdapter(sync_session)
        response = await auth_runtime.api_routes.login(
            auth_runtime.schemas.LoginRequest(
                email="team@example.com",
                password="password123",
            ),
            session=session,
            settings=settings,
        )

    assert response.token_type == "bearer"
    assert response.access_token


@pytest.mark.anyio
async def test_me(auth_runtime):
    settings = auth_runtime.core_config.get_settings()

    with auth_runtime.session_factory() as sync_session:
        session = AsyncSessionAdapter(sync_session)
        await auth_runtime.api_routes.register(
            auth_runtime.schemas.RegisterRequest(
                email="team@example.com",
                password="password123",
                full_name="Hack Team",
            ),
            session=session,
            settings=settings,
        )

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/me",
            "headers": [],
            "query_string": b"",
            "state": {},
        },
        receive=receive,
    )
    request.state.user_id = "1"

    with auth_runtime.session_factory() as sync_session:
        session = AsyncSessionAdapter(sync_session)
        current_user = await auth_runtime.api_dependencies.get_current_user(
            request,
            session=session,
        )
    response = await auth_runtime.api_routes.me(current_user)

    assert response.model_dump() == {
        "id": 1,
        "email": "team@example.com",
        "full_name": "Hack Team",
    }


@pytest.mark.anyio
async def test_register_duplicate_email(auth_runtime):
    settings = auth_runtime.core_config.get_settings()
    payload = auth_runtime.schemas.RegisterRequest(
        email="team@example.com",
        password="password123",
        full_name="Hack Team",
    )

    with auth_runtime.session_factory() as sync_session:
        session = AsyncSessionAdapter(sync_session)
        await auth_runtime.api_routes.register(payload, session=session, settings=settings)

    with auth_runtime.session_factory() as sync_session:
        session = AsyncSessionAdapter(sync_session)
        with pytest.raises(HTTPException) as exc_info:
            await auth_runtime.api_routes.register(payload, session=session, settings=settings)

    error = exc_info.value
    assert isinstance(error, HTTPException)
    assert error.status_code == 409
    assert "already" in str(error.detail).lower()


@pytest.mark.anyio
async def test_login_wrong_password(auth_runtime):
    settings = auth_runtime.core_config.get_settings()

    with auth_runtime.session_factory() as sync_session:
        session = AsyncSessionAdapter(sync_session)
        await auth_runtime.api_routes.register(
            auth_runtime.schemas.RegisterRequest(
                email="team@example.com",
                password="password123",
                full_name="Hack Team",
            ),
            session=session,
            settings=settings,
        )

    with auth_runtime.session_factory() as sync_session:
        session = AsyncSessionAdapter(sync_session)
        with pytest.raises(HTTPException) as exc_info:
            await auth_runtime.api_routes.login(
                auth_runtime.schemas.LoginRequest(
                    email="team@example.com",
                    password="wrong-password",
                ),
                session=session,
                settings=settings,
            )

    error = exc_info.value
    assert isinstance(error, HTTPException)
    assert error.status_code == 401
