"""Rate-limited HTTP client for the Central API.

Every service that calls https://technocracy.brittoo.xyz MUST use
CentralAPIClient from this module. Never use httpx directly for Central
API calls.

The sliding-window limiter holds each service process to 20 requests per
minute. The Central API's hard limit is 30 req/min per token; the 10
req/min headroom protects against penalty (-20 pts per violation) even
when multiple services are active simultaneously.

If a call would push the service over the limit, the coroutine waits
(backpressure) until a slot opens. Callers are never rejected for rate
reasons — they are delayed.
"""

import asyncio
import time
from collections import deque

import httpx
from fastapi import HTTPException


class _SlidingWindowLimiter:
    """Asyncio-safe sliding-window rate limiter."""

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
                # Block until the oldest call falls outside the window
                sleep_for = self._timestamps[0] + self._window - now
                if sleep_for > 0:
                    await asyncio.sleep(sleep_for)
                # Re-evict after sleep
                now = time.monotonic()
                cutoff = now - self._window
                while self._timestamps and self._timestamps[0] <= cutoff:
                    self._timestamps.popleft()

            self._timestamps.append(time.monotonic())

    @property
    def remaining(self) -> int:
        """Approximate remaining calls in the current window (not lock-protected)."""
        now = time.monotonic()
        cutoff = now - self._window
        active = sum(1 for t in self._timestamps if t > cutoff)
        return max(0, self._max - active)


# Module-level singleton: one limiter per service process.
# 20 req/min ceiling — 10 below the Central API hard limit.
_limiter = _SlidingWindowLimiter(max_calls=20, window_seconds=60.0)


class CentralAPIClient:
    """Rate-limited, error-normalising HTTP client for the Central API.

    Instantiate once per request (or as a dependency) using the service's
    settings. All network errors and non-200 responses are translated into
    FastAPI HTTPException so route handlers stay clean.

    Usage::

        client = CentralAPIClient(settings.central_api_url, settings.central_api_token)
        data = await client.get("/api/data/products", params={"category": "TOOLS"})
    """

    def __init__(self, base_url: str, token: str, timeout: float = 15.0) -> None:
        self._base = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    async def get(self, path: str, params: dict | None = None) -> dict:
        """Make a rate-limited GET to the Central API and return the parsed JSON body.

        Raises HTTPException on any error (timeout, network failure, non-200).
        """
        await _limiter.acquire()
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
