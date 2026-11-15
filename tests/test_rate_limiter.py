import pytest

from app.core.exceptions import RateLimitError
from app.core.rate_limit import InMemoryRateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_blocks_after_limit_with_retry_after() -> None:
    limiter = InMemoryRateLimiter(FakeClock())
    for _ in range(3):
        limiter.check("k", limit=3, window_seconds=60)
    with pytest.raises(RateLimitError) as exc:
        limiter.check("k", limit=3, window_seconds=60)
    assert exc.value.headers == {"Retry-After": "60"}


def test_allows_again_after_window() -> None:
    clock = FakeClock()
    limiter = InMemoryRateLimiter(clock)
    for _ in range(3):
        limiter.check("k", limit=3, window_seconds=60)
    clock.now += 61
    limiter.check("k", limit=3, window_seconds=60)


def test_keys_are_independent() -> None:
    limiter = InMemoryRateLimiter(FakeClock())
    limiter.check("a", limit=1, window_seconds=60)
    limiter.check("b", limit=1, window_seconds=60)


def test_sweep_bounds_memory() -> None:
    clock = FakeClock()
    limiter = InMemoryRateLimiter(clock)
    limiter.MAX_KEYS = 5
    for i in range(10):
        limiter.check(f"k{i}", limit=1, window_seconds=60)
    clock.now += 120
    limiter.check("fresh", limit=1, window_seconds=60)
    assert len(limiter._hits) == 1
