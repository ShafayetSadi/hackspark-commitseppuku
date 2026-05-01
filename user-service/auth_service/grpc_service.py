import grpc
import grpc.aio
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.core.config import get_settings
from auth_service.db.session import SessionLocal
from auth_service.schemas.auth import LoginRequest, RegisterRequest
from auth_service.services.auth_service import login_user, register_user
from auth_service.services.errors import DuplicateEmailError, InvalidCredentialsError
from shared.app_core.database import session_dependency
from shared.app_core.logging import get_logger
from shared.grpc_gen import user_pb2, user_pb2_grpc

logger = get_logger("user-service")


class UserServicer(user_pb2_grpc.UserServiceServicer):
    def __init__(self) -> None:
        self._settings = get_settings()

    async def _get_session(self) -> AsyncSession:
        async for session in session_dependency(SessionLocal):
            return session

    async def Register(self, request: user_pb2.RegisterRequest, context: grpc.aio.ServicerContext):
        logger.info("grpc_register", email=request.email)
        try:
            async for session in session_dependency(SessionLocal):
                payload = RegisterRequest(
                    email=request.email,
                    password=request.password,
                    name=request.full_name,
                )
                result = await register_user(session, payload, self._settings)
                return user_pb2.AuthResponse(
                    access_token=result["token"],
                    token_type="bearer",
                )
        except DuplicateEmailError as exc:
            await context.abort(grpc.StatusCode.ALREADY_EXISTS, str(exc))
        except Exception as exc:
            logger.error("register_error", error=str(exc))
            await context.abort(grpc.StatusCode.INTERNAL, "Internal error")

    async def Login(self, request: user_pb2.LoginRequest, context: grpc.aio.ServicerContext):
        logger.info("grpc_login", email=request.email)
        try:
            async for session in session_dependency(SessionLocal):
                payload = LoginRequest(email=request.email, password=request.password)
                token = await login_user(session, payload, self._settings)
                return user_pb2.AuthResponse(access_token=token, token_type="bearer")
        except InvalidCredentialsError as exc:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, str(exc))
        except Exception as exc:
            logger.error("login_error", error=str(exc))
            await context.abort(grpc.StatusCode.INTERNAL, "Internal error")

    async def Me(self, request: user_pb2.MeRequest, context: grpc.aio.ServicerContext):
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
                return user_pb2.UserResponse(id=user.id, email=user.email, full_name=user.full_name)
        except Exception as exc:
            logger.error("me_error", error=str(exc))
            await context.abort(grpc.StatusCode.INTERNAL, "Internal error")
