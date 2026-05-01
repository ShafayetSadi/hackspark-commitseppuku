from typing import Any, cast

import grpc
import grpc.aio
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.core.config import get_settings
from auth_service.db.session import SessionLocal
from auth_service.schemas.auth import LoginRequest, RegisterRequest
from auth_service.services.auth_service import login_user, register_user
from auth_service.services.discount import get_user_discount
from auth_service.services.errors import DuplicateEmailError, InvalidCredentialsError
from shared.app_core.central_api import CentralAPIClient
from shared.app_core.database import session_dependency
from shared.app_core.logging import get_logger
from shared.grpc_gen import user_pb2, user_pb2_grpc

logger = get_logger("user-service")
USER_PB2 = cast(Any, user_pb2)


class UserServicer(user_pb2_grpc.UserServiceServicer):
    def __init__(self) -> None:
        self._settings = get_settings()

    async def _get_session(self) -> AsyncSession:
        async for session in session_dependency(SessionLocal):
            return session
        raise RuntimeError("Database session unavailable")

    def _central_client(self) -> CentralAPIClient:
        return CentralAPIClient(
            self._settings.central_api_url,
            self._settings.central_api_token,
            redis_url=self._settings.central_api_redis_url,
            max_calls=self._settings.central_api_rate_limit,
            window_seconds=self._settings.central_api_rate_window_seconds,
        )

    async def Register(self, request: Any, context: grpc.aio.ServicerContext):
        logger.info("grpc_register", email=request.email)
        try:
            async for session in session_dependency(SessionLocal):
                payload = RegisterRequest(
                    email=request.email,
                    password=request.password,
                    name=request.full_name,
                )
                result = await register_user(session, payload, self._settings)
                return USER_PB2.AuthResponse(
                    access_token=result["token"],
                    token_type="bearer",
                )
        except DuplicateEmailError as exc:
            await context.abort(grpc.StatusCode.ALREADY_EXISTS, str(exc))
        except ValidationError as exc:
            logger.warning("register_validation_error", error=str(exc), email=request.email)
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except Exception as exc:
            logger.error("register_error", error=str(exc))
            await context.abort(grpc.StatusCode.INTERNAL, "Internal error")

    async def Login(self, request: Any, context: grpc.aio.ServicerContext):
        logger.info("grpc_login", email=request.email)
        try:
            async for session in session_dependency(SessionLocal):
                payload = LoginRequest(email=request.email, password=request.password)
                token = await login_user(session, payload, self._settings)
                return USER_PB2.AuthResponse(access_token=token, token_type="bearer")
        except InvalidCredentialsError as exc:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, str(exc))
        except ValidationError as exc:
            logger.warning("login_validation_error", error=str(exc), email=request.email)
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except Exception as exc:
            logger.error("login_error", error=str(exc))
            await context.abort(grpc.StatusCode.INTERNAL, "Internal error")

    async def Me(self, request: Any, context: grpc.aio.ServicerContext):
        from sqlalchemy import select

        from auth_service.models.user import User

        if not request.user_id:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Missing user_id")
            return

        try:
            async for session in session_dependency(SessionLocal):
                user = await session.scalar(select(User).where(User.id == int(request.user_id)))
                if not user:
                    await context.abort(grpc.StatusCode.NOT_FOUND, "User not found")
                    return
                return USER_PB2.UserResponse(id=user.id, email=user.email, full_name=user.full_name)
        except Exception as exc:
            logger.error("me_error", error=str(exc))
            await context.abort(grpc.StatusCode.INTERNAL, "Internal error")

    async def GetDiscount(self, request: Any, context: grpc.aio.ServicerContext):
        logger.info("grpc_get_discount", user_id=request.user_id)
        try:
            data = await get_user_discount(self._central_client(), user_id=request.user_id)
            return USER_PB2.DiscountResponse(
                user_id=data["userId"],
                security_score=data["securityScore"],
                discount_percent=data["discountPercent"],
            )
        except HTTPException as exc:
            status_map = {
                400: grpc.StatusCode.INVALID_ARGUMENT,
                404: grpc.StatusCode.NOT_FOUND,
                429: grpc.StatusCode.RESOURCE_EXHAUSTED,
                502: grpc.StatusCode.UNAVAILABLE,
                504: grpc.StatusCode.DEADLINE_EXCEEDED,
            }
            await context.abort(
                status_map.get(exc.status_code, grpc.StatusCode.INTERNAL), str(exc.detail)
            )
        except Exception as exc:
            logger.error("discount_error", error=str(exc))
            await context.abort(grpc.StatusCode.INTERNAL, "Internal error")
