from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

from high_load_ai.core.container import Container
from high_load_ai.core.security import require_api_key


def get_container(request: Request) -> Container:
    return request.app.state.container  # type: ignore[no-any-return]


async def enforce_rate_limit(
    request: Request,
    container: Container = Depends(get_container),
    api_key: str = Depends(require_api_key),
) -> None:
    route_key = request.url.path
    key = f"{api_key}:{route_key}"
    allowed, remaining_or_retry = await container.rate_limiter.allow(
        key=key,
        limit=container.settings.rate_limit_max_requests,
        window_seconds=container.settings.rate_limit_window_seconds,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(remaining_or_retry)},
        )
