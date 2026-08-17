"""In-memory IP rate limiter for contact submissions."""

from __future__ import annotations

from collections import defaultdict, deque
from time import monotonic


class RateLimiter:
    def __init__(self, max_requests: int = 5, window_seconds: int = 600) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = monotonic()
        bucket = self._hits[key]
        window = self.window_seconds
        while bucket and now - bucket[0] > window:
            bucket.popleft()
        if len(bucket) >= self.max_requests:
            return False
        bucket.append(now)
        return True
