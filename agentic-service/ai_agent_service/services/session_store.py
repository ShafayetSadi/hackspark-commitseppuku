"""MongoDB-backed conversation session store."""

import uuid
from datetime import UTC, datetime

import motor.motor_asyncio

_client: motor.motor_asyncio.AsyncIOMotorClient | None = None
_db = None


def init_mongo(uri: str) -> None:
    global _client, _db
    _client = motor.motor_asyncio.AsyncIOMotorClient(uri)
    _db = _client.get_default_database()


def _sessions():
    if _db is None:
        raise RuntimeError("MongoDB not initialised — call init_mongo first")
    return _db["sessions"]


def new_session_id() -> str:
    return str(uuid.uuid4())


async def load_history(session_id: str) -> list[dict]:
    doc = await _sessions().find_one({"session_id": session_id})
    if doc:
        return doc.get("messages", [])
    return []


async def append_message(session_id: str, role: str, content: str) -> None:
    message = {"role": role, "content": content, "ts": datetime.now(UTC).isoformat()}
    await _sessions().update_one(
        {"session_id": session_id},
        {"$push": {"messages": message}, "$setOnInsert": {"session_id": session_id}},
        upsert=True,
    )
