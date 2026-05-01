from auth_service.core.config import AuthSettings
from auth_service.models.user import User
from auth_service.schemas.auth import LoginRequest, RegisterRequest
from auth_service.services.errors import DuplicateEmailError, InvalidCredentialsError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.app_core.security import (
    create_access_token,
    hash_password,
    verify_password,
)


async def register_user(
    session: AsyncSession, payload: RegisterRequest, settings: AuthSettings
) -> dict:
    existing = await session.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise DuplicateEmailError("Email already registered")

    user = User(
        email=payload.email,
        full_name=payload.name,
        hashed_password=hash_password(payload.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    token = create_access_token(
        subject=str(user.id),
        secret=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
        expires_minutes=settings.access_token_expire_minutes,
    )
    return {"user": user, "token": token}


async def login_user(session: AsyncSession, payload: LoginRequest, settings: AuthSettings) -> str:
    user = await session.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise InvalidCredentialsError("Invalid credentials")
    return create_access_token(
        subject=str(user.id),
        secret=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
        expires_minutes=settings.access_token_expire_minutes,
    )
