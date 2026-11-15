"""Rate limiting implementation."""

import math
import time
from collections import deque
from collections.abc import Callable
from functools import lru_cache
from threading import Lock

from app.core.exceptions import RateLimitError


class InMemoryRateLimiter:
    """Sliding window rate limiter in memory. Pre-process only: swap out for Redis if needed."""

    MAX_KEYS = 1000

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._windows: dict[str, int] = {}
        self._lock = Lock()

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        now = self._clock()
        cutoff = now - window_seconds
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= limit:
                retry_after = max(1, math.ceil(hits[0] + window_seconds - now))
                raise RateLimitError(retry_after)
            hits.append(now)
            self._windows[key] = window_seconds
            if len(self._hits) > self.MAX_KEYS:
                self._sweep(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()
            self._windows.clear()

    def _sweep(self, now: float) -> None:
        stale = [
            key
            for key, hits in self._hits.items()
            if not hits or hits[-1] <= now - self._windows[key]
        ]
        for key in stale:
            del self._hits[key]
            del self._windows[key]


@lru_cache
def get_rate_limiter() -> InMemoryRateLimiter:
    return InMemoryRateLimiter()
