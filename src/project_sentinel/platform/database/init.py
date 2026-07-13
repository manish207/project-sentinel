from project_sentinel.platform.database.base import Base
from project_sentinel.platform.database.engine import get_engine
from sqlalchemy import text


async def init_database(database_url: str | None = None) -> None:
    from project_sentinel.platform.database import models as _models

    _ = _models
    engine = get_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        if engine.url.get_backend_name() == "sqlite":
            await _migrate_sqlite(connection)


async def _migrate_sqlite(connection) -> None:
    task_columns = await _sqlite_columns(connection, "tasks")
    migrations = {
        "tags": "ALTER TABLE tasks ADD COLUMN tags TEXT NOT NULL DEFAULT '[]'",
        "due_date": "ALTER TABLE tasks ADD COLUMN due_date DATE",
        "scheduled_date": "ALTER TABLE tasks ADD COLUMN scheduled_date DATE",
        "completed_at": "ALTER TABLE tasks ADD COLUMN completed_at DATETIME",
        "estimated_minutes": "ALTER TABLE tasks ADD COLUMN estimated_minutes INTEGER",
        "actual_minutes": "ALTER TABLE tasks ADD COLUMN actual_minutes INTEGER",
        "parent_task_id": "ALTER TABLE tasks ADD COLUMN parent_task_id VARCHAR(36)",
        "workspace_id": "ALTER TABLE tasks ADD COLUMN workspace_id VARCHAR(36)",
        "start_time": "ALTER TABLE tasks ADD COLUMN start_time DATETIME",
        "end_time": "ALTER TABLE tasks ADD COLUMN end_time DATETIME",
    }
    for column, statement in migrations.items():
        if column not in task_columns:
            await connection.execute(text(statement))

    workspace_columns = await _sqlite_columns(connection, "workspaces")
    if "is_default" not in workspace_columns:
        await connection.execute(
            text(
                "ALTER TABLE workspaces "
                "ADD COLUMN is_default BOOLEAN NOT NULL DEFAULT 0"
            )
        )


async def _sqlite_columns(connection, table_name: str) -> set[str]:
    result = await connection.execute(text(f"PRAGMA table_info({table_name})"))
    return {row[1] for row in result}
