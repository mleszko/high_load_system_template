from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from high_load_ai.core.config import Settings


def build_session_factory(settings: Settings) -> async_sessionmaker[AsyncSession]:
    connect_args: dict[str, object] = {}
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=not settings.database_url.startswith("sqlite"),
        connect_args=connect_args,
    )
    return async_sessionmaker(engine, expire_on_commit=False)
