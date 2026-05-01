from auth_service.api.dependencies import get_current_user
from auth_service.core.config import AuthSettings, get_settings
from auth_service.db.session import get_db_session
from auth_service.models.user import User
from auth_service.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from auth_service.services.auth_service import login_user, register_user
from auth_service.services.errors import DuplicateEmailError, InvalidCredentialsError
from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/status")
async def status() -> dict:
    return {"service": "user-service", "status": "OK"}


@router.get("/health")
async def healthcheck() -> dict:
    return {"status": "ok", "service": "user-service"}


@router.post("/register", response_model=TokenResponse, status_code=http_status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: AuthSettings = Depends(get_settings),
) -> TokenResponse:
    try:
        result = await register_user(session, payload, settings)
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return TokenResponse(access_token=result["token"])


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: AuthSettings = Depends(get_settings),
) -> TokenResponse:
    try:
        token = await login_user(session, payload, settings)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.from_model(current_user)
