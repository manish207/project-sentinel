from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "sqlite+aiosqlite:///sentinel.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)
