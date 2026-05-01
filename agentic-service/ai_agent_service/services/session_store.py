"""Redis-backed conversation session store."""

import uuid
from datetime import UTC, datetime

from ai_agent_service.services.redis_client import RedisClient

_client: RedisClient | None = None
_ttl_seconds: int | None = None


def init_redis(url: str, ttl_seconds: int | None = None) -> None:
    global _client, _ttl_seconds
    _client = RedisClient(url)
    _ttl_seconds = ttl_seconds if ttl_seconds and ttl_seconds > 0 else None


def _redis() -> RedisClient:
    if _client is None:
        raise RuntimeError("Redis not initialised — call init_redis first")
    return _client


def _meta_key(session_id: str) -> str:
    return f"session:{session_id}:meta"


def _messages_key(session_id: str) -> str:
    return f"session:{session_id}:messages"


def _summary_key(session_id: str) -> str:
    return f"session:{session_id}:summary"


def new_session_id() -> str:
    return str(uuid.uuid4())


async def ping() -> bool:
    return await _redis().ping()


async def load_recent_messages(session_id: str, limit: int) -> list[dict]:
    if limit <= 0:
        return []
    return await _redis().lrange_json(_messages_key(session_id), -limit, -1)


async def load_history(session_id: str) -> list[dict]:
    return await _redis().lrange_json(_messages_key(session_id), 0, -1)


async def load_summary(session_id: str) -> str:
    return await _redis().get(_summary_key(session_id)) or ""


async def load_meta(session_id: str) -> dict:
    return await _redis().get_json(_meta_key(session_id)) or {}


async def ensure_session_meta(session_id: str, name: str, summary: str = "") -> dict:
    existing = await load_meta(session_id)
    if existing:
        return existing

    meta = {
        "name": name,
        "summary": summary,
        "lastMessageAt": datetime.now(UTC).isoformat(),
    }
    await _redis().set_json(_meta_key(session_id), meta)
    await _apply_ttl(session_id)
    return meta


async def append_message(session_id: str, role: str, content: str) -> None:
    message = {"role": role, "content": content, "ts": datetime.now(UTC).isoformat()}
    await _redis().rpush_json(_messages_key(session_id), message)
    await _apply_ttl(session_id)


async def update_summary(session_id: str, summary: str) -> None:
    await _redis().set(_summary_key(session_id), summary)
    meta = await load_meta(session_id)
    meta["summary"] = summary
    meta["lastMessageAt"] = datetime.now(UTC).isoformat()
    if "name" not in meta:
        meta["name"] = "Untitled Chat"
    await _redis().set_json(_meta_key(session_id), meta)
    await _apply_ttl(session_id)


async def touch_meta(session_id: str, *, name: str | None = None) -> None:
    meta = await load_meta(session_id)
    if name and not meta.get("name"):
        meta["name"] = name
    meta.setdefault("name", "Untitled Chat")
    meta.setdefault("summary", await load_summary(session_id))
    meta["lastMessageAt"] = datetime.now(UTC).isoformat()
    await _redis().set_json(_meta_key(session_id), meta)
    await _apply_ttl(session_id)


async def list_sessions() -> list[dict]:
    sessions: list[dict] = []
    async for key in _redis().scan_iter("session:*:meta"):
        session_id = key.split(":")[1]
        meta = await load_meta(session_id)
        if not meta:
            continue
        sessions.append(
            {
                "session_id": session_id,
                "name": meta.get("name", "Untitled Chat"),
                "summary": meta.get("summary", ""),
                "last_message_at": meta.get("lastMessageAt", ""),
            }
        )
    sessions.sort(key=lambda item: item["last_message_at"], reverse=True)
    return sessions


async def delete_session(session_id: str) -> bool:
    deleted = await _redis().delete(
        _meta_key(session_id),
        _messages_key(session_id),
        _summary_key(session_id),
    )
    return deleted > 0


async def _apply_ttl(session_id: str) -> None:
    if _ttl_seconds is None:
        return

    redis = _redis()
    await redis.expire(_meta_key(session_id), _ttl_seconds)
    await redis.expire(_messages_key(session_id), _ttl_seconds)
    await redis.expire(_summary_key(session_id), _ttl_seconds)
