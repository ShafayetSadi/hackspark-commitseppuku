"""Rate-limited HTTP client for the Central API.

Every service that calls https://technocracy.brittoo.xyz MUST use
CentralAPIClient from this module. Never use httpx directly for Central
API calls.

The preferred limiter uses Redis so all services in the stack share one
20 req/min sliding window. If Redis is unavailable, the client falls back
to a process-local limiter so the service still behaves safely in
standalone contexts.
"""

import asyncio
import hashlib
import time
import uuid
from collections import deque
from dataclasses import dataclass

import httpx
from fastapi import HTTPException
from redis import asyncio as redis_asyncio
from redis.exceptions import RedisError


class _SlidingWindowLimiter:
    """Asyncio-safe process-local sliding-window rate limiter."""

    def __init__(self, max_calls: int, window_seconds: float) -> None:
        self._max = max_calls
        self._window = window_seconds
        self._timestamps: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            cutoff = now - self._window
            while self._timestamps and self._timestamps[0] <= cutoff:
                self._timestamps.popleft()

            if len(self._timestamps) >= self._max:
                sleep_for = self._timestamps[0] + self._window - now
                if sleep_for > 0:
                    await asyncio.sleep(sleep_for)

                now = time.monotonic()
                cutoff = now - self._window
                while self._timestamps and self._timestamps[0] <= cutoff:
                    self._timestamps.popleft()

            self._timestamps.append(time.monotonic())


_REDIS_ACQUIRE_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window_seconds = tonumber(ARGV[2])
local max_calls = tonumber(ARGV[3])
local member = ARGV[4]
local cutoff = now - window_seconds

redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)

local count = redis.call('ZCARD', key)
if count < max_calls then
  redis.call('ZADD', key, now, member)
  redis.call('EXPIRE', key, math.ceil(window_seconds) + 1)
  return {1, 0}
end

local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
if oldest[2] == nil then
  return {1, 0}
end

local retry_after = tonumber(oldest[2]) + window_seconds - now
if retry_after < 0 then
  retry_after = 0
end
return {0, retry_after}
"""


class _RedisSlidingWindowLimiter:
    """Redis-backed sliding-window limiter shared across services."""

    def __init__(self, redis_url: str, key: str, max_calls: int, window_seconds: float) -> None:
        self._client = redis_asyncio.from_url(redis_url, decode_responses=True)
        self._key = key
        self._max = max_calls
        self._window = window_seconds

    async def acquire(self) -> None:
        while True:
            now = time.time()
            allowed, retry_after = await self._client.eval(
                _REDIS_ACQUIRE_SCRIPT,
                1,
                self._key,
                str(now),
                str(self._window),
                str(self._max),
                f"{now}:{uuid.uuid4()}",
            )
            if int(allowed) == 1:
                return
            await asyncio.sleep(max(float(retry_after), 0.01))


@dataclass(frozen=True, slots=True)
class _LimiterConfig:
    redis_url: str | None
    token_hash: str
    max_calls: int
    window_seconds: float


_local_limiters: dict[_LimiterConfig, _SlidingWindowLimiter] = {}
_redis_limiters: dict[_LimiterConfig, _RedisSlidingWindowLimiter] = {}
_limiter_lock = asyncio.Lock()


async def _get_limiter(config: _LimiterConfig) -> _RedisSlidingWindowLimiter | _SlidingWindowLimiter:
    async with _limiter_lock:
        if config.redis_url:
            redis_limiter = _redis_limiters.get(config)
            if redis_limiter is None:
                redis_limiter = _RedisSlidingWindowLimiter(
                    config.redis_url,
                    f"central-api:window:{config.token_hash}",
                    config.max_calls,
                    config.window_seconds,
                )
                _redis_limiters[config] = redis_limiter
            return redis_limiter

        local_limiter = _local_limiters.get(config)
        if local_limiter is None:
            local_limiter = _SlidingWindowLimiter(config.max_calls, config.window_seconds)
            _local_limiters[config] = local_limiter
        return local_limiter


class CentralAPIClient:
    """Rate-limited, error-normalising HTTP client for the Central API."""

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: float = 15.0,
        *,
        redis_url: str | None = None,
        max_calls: int = 20,
        window_seconds: float = 60.0,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout
        self._config = _LimiterConfig(
            redis_url=redis_url.strip() if redis_url else None,
            token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest()[:16],
            max_calls=max_calls,
            window_seconds=window_seconds,
        )

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    async def _acquire(self) -> None:
        limiter = await _get_limiter(self._config)
        try:
            await limiter.acquire()
        except RedisError:
            fallback = await _get_limiter(
                _LimiterConfig(
                    redis_url=None,
                    token_hash=self._config.token_hash,
                    max_calls=self._config.max_calls,
                    window_seconds=self._config.window_seconds,
                )
            )
            await fallback.acquire()

    async def get(self, path: str, params: dict | None = None) -> dict:
        """Make a rate-limited GET to the Central API and return the parsed JSON body."""
        await self._acquire()
        url = f"{self._base}{path}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(url, params=params or {}, headers=self._headers())
        except httpx.TimeoutException as exc:
            raise HTTPException(status_code=504, detail="Central API timeout") from exc
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail="Central API unreachable") from exc

        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Resource not found")
        if resp.status_code == 429:
            raise HTTPException(
                status_code=429,
                detail="Central API rate limit exceeded — should not happen; check limiter config",
            )
        raise HTTPException(status_code=502, detail=f"Central API error {resp.status_code}")
