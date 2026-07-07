from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from .engine import engine

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
