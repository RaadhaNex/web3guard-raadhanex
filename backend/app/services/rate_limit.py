from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.core.config import settings

_BUCKETS: dict[str, deque[datetime]] = defaultdict(deque)


def enforce_hourly_limit(
    key: str,
    *,
    limit: int | None = None,
    label: str = "Request",
) -> None:
    """Small in-memory MVP rate limiter.

    Real production note: this limiter is process-local. It is safe for a single
    small Render instance, but high-scale deployments should move counters to
    Redis/Upstash so limits are shared across instances.
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
            detail={
                "message": f"{label} rate limit reached. Try again later.",
                "limit": max_requests,
                "window": "1 hour",
                "real_only_note": "The request was blocked instead of returning a fake scan result.",
            },
        )

    bucket.append(now)


def reset_rate_limits_for_tests() -> None:
    _BUCKETS.clear()
