from collections.abc import AsyncIterator

from auth_service.core.config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession

from shared.app_core.database import build_engine, build_session_factory, session_dependency

settings = get_settings()
engine = build_engine(settings.database_url)
SessionLocal = build_session_factory(engine)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async for session in session_dependency(SessionLocal):
        yield session
