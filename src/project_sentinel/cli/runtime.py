from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from project_sentinel.platform.database import get_sessionmaker, init_database


async def with_session[T](action: Callable[[AsyncSession], Awaitable[T]]) -> T:
    await init_database()
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        return await action(session)
