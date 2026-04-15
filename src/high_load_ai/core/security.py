from fastapi import Header, HTTPException, status

from high_load_ai.core.config import get_settings


def _parse_api_keys(raw: str) -> set[str]:
    return {part.strip() for part in raw.split(",") if part.strip()}


async def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> str:
    settings = get_settings()
    allowed = _parse_api_keys(settings.api_keys)
    bearer_value = authorization.removeprefix("Bearer ").strip() if authorization else None
    presented = (x_api_key or bearer_value or "").strip()
    if not presented or presented not in allowed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return presented
