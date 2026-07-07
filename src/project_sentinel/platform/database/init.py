from project_sentinel.platform.database.base import Base
from project_sentinel.platform.database.engine import get_engine


async def init_database(database_url: str | None = None) -> None:
    from project_sentinel.platform.database import models as _models

    _ = _models
    engine = get_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
