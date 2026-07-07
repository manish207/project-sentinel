from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from .engine import get_engine


def get_sessionmaker(
    database_url: str | None = None,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=get_engine(database_url),
        class_=AsyncSession,
        expire_on_commit=False,
    )


AsyncSessionLocal = get_sessionmaker()
