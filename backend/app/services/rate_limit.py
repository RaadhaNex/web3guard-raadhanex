from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.core.config import settings

_BUCKETS: dict[str, deque[datetime]] = defaultdict(deque)


def enforce_hourly_limit(key: str, *, limit: int | None = None) -> None:
    """Small in-memory MVP rate limiter.

    This is intentionally simple for current.5. Production should move this to Redis/Upstash
    so limits work across multiple Render instances.
    """
    max_requests = limit or settings.max_url_scan_per_hour
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=1)
    bucket = _BUCKETS[key]
    while bucket and bucket[0] < window_start:
        bucket.popleft()
    if len(bucket) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Website passive scan rate limit reached. Try again later. Current limit: {max_requests} scans/hour.",
        )
    bucket.append(now)


def reset_rate_limits_for_tests() -> None:
    _BUCKETS.clear()
