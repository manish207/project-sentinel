from functools import lru_cache
from os import environ

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from project_sentinel.config.defaults import DEFAULT_DATABASE_URL


def get_database_url() -> str:
    return environ.get("SENTINEL_DATABASE_URL", DEFAULT_DATABASE_URL)


@lru_cache(maxsize=None)
def get_engine(database_url: str | None = None) -> AsyncEngine:
    return create_async_engine(
        database_url or get_database_url(),
        echo=False,
        future=True,
    )


engine = get_engine()
