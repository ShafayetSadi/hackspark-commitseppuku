import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from urllib.parse import unquote, urlparse


class RedisProtocolError(RuntimeError):
    """Raised when Redis returns an unexpected response."""


@dataclass(slots=True)
class RedisConnectionSettings:
    host: str
    port: int
    db: int
    password: str | None


def parse_redis_url(url: str) -> RedisConnectionSettings:
    parsed = urlparse(url)
    if parsed.scheme != "redis":
        raise ValueError("Redis URL must use the redis:// scheme")

    host = parsed.hostname or "localhost"
    port = parsed.port or 6379
    db = int(parsed.path.removeprefix("/") or "0")
    password = unquote(parsed.password) if parsed.password else None
    return RedisConnectionSettings(host=host, port=port, db=db, password=password)


class RedisClient:
    def __init__(self, url: str) -> None:
        self._settings = parse_redis_url(url)

    async def ping(self) -> bool:
        return (await self._execute("PING")) == "PONG"

    async def get(self, key: str) -> str | None:
        value = await self._execute("GET", key)
        return value if isinstance(value, str | None) else None

    async def set(self, key: str, value: str) -> None:
        await self._execute("SET", key, value)

    async def rpush(self, key: str, *values: str) -> int:
        response = await self._execute("RPUSH", key, *values)
        if not isinstance(response, int):
            raise RedisProtocolError("RPUSH returned a non-integer response")
        return response

    async def lrange(self, key: str, start: int, stop: int) -> list[str]:
        response = await self._execute("LRANGE", key, str(start), str(stop))
        if not isinstance(response, list):
            raise RedisProtocolError("LRANGE returned a non-list response")
        return [item for item in response if isinstance(item, str)]

    async def delete(self, *keys: str) -> int:
        response = await self._execute("DEL", *keys)
        if not isinstance(response, int):
            raise RedisProtocolError("DEL returned a non-integer response")
        return response

    async def expire(self, key: str, seconds: int) -> bool:
        response = await self._execute("EXPIRE", key, str(seconds))
        if not isinstance(response, int):
            raise RedisProtocolError("EXPIRE returned a non-integer response")
        return response == 1

    async def scan(self, cursor: int, match: str, count: int = 50) -> tuple[int, list[str]]:
        response = await self._execute(
            "SCAN",
            str(cursor),
            "MATCH",
            match,
            "COUNT",
            str(count),
        )
        if not isinstance(response, list) or len(response) != 2:
            raise RedisProtocolError("SCAN returned an unexpected response")

        next_cursor_raw, keys_raw = response
        next_cursor = int(next_cursor_raw) if isinstance(next_cursor_raw, str) else 0
        keys = [item for item in keys_raw if isinstance(item, str)] if isinstance(keys_raw, list) else []
        return next_cursor, keys

    async def scan_iter(self, match: str, count: int = 50) -> AsyncIterator[str]:
        cursor = 0
        while True:
            cursor, keys = await self.scan(cursor, match=match, count=count)
            for key in keys:
                yield key
            if cursor == 0:
                return

    async def get_json(self, key: str) -> dict | None:
        raw = await self.get(key)
        return json.loads(raw) if raw else None

    async def set_json(self, key: str, value: dict) -> None:
        await self.set(key, json.dumps(value))

    async def rpush_json(self, key: str, *values: dict) -> int:
        encoded = [json.dumps(value) for value in values]
        return await self.rpush(key, *encoded)

    async def lrange_json(self, key: str, start: int, stop: int) -> list[dict]:
        values = await self.lrange(key, start, stop)
        return [json.loads(value) for value in values]

    async def _execute(self, *parts: str) -> str | int | list | None:
        reader, writer = await asyncio.open_connection(
            self._settings.host,
            self._settings.port,
        )
        try:
            if self._settings.password:
                await self._send_command(writer, "AUTH", self._settings.password)
                await self._read_response(reader)

            if self._settings.db:
                await self._send_command(writer, "SELECT", str(self._settings.db))
                await self._read_response(reader)

            await self._send_command(writer, *parts)
            return await self._read_response(reader)
        finally:
            writer.close()
            await writer.wait_closed()

    async def _send_command(self, writer: asyncio.StreamWriter, *parts: str) -> None:
        writer.write(f"*{len(parts)}\r\n".encode())
        for part in parts:
            encoded = part.encode()
            writer.write(f"${len(encoded)}\r\n".encode())
            writer.write(encoded + b"\r\n")
        await writer.drain()

    async def _read_response(self, reader: asyncio.StreamReader) -> str | int | list | None:
        prefix = await reader.readexactly(1)
        if prefix == b"+":
            return (await reader.readline()).rstrip(b"\r\n").decode()
        if prefix == b"$":
            size = int((await reader.readline()).rstrip(b"\r\n"))
            if size == -1:
                return None
            data = await reader.readexactly(size)
            await reader.readexactly(2)
            return data.decode()
        if prefix == b":":
            return int((await reader.readline()).rstrip(b"\r\n"))
        if prefix == b"*":
            count = int((await reader.readline()).rstrip(b"\r\n"))
            if count == -1:
                return []
            return [await self._read_response(reader) for _ in range(count)]
        if prefix == b"-":
            message = (await reader.readline()).rstrip(b"\r\n").decode()
            raise RedisProtocolError(message)
        raise RedisProtocolError(f"Unsupported Redis response prefix: {prefix!r}")
