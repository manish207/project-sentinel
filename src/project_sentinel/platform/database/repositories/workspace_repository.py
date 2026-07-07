from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from project_sentinel.domain.common import AuditInfo
from project_sentinel.domain.workspace import Workspace
from project_sentinel.platform.database.models import WorkspaceRecord


class SqlAlchemyWorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, workspace: Workspace) -> Workspace:
        if workspace.is_default:
            await self._clear_default()
        self._session.add(self._to_record(workspace))
        await self._session.commit()
        return workspace

    async def list(self) -> list[Workspace]:
        result = await self._session.execute(
            select(WorkspaceRecord).order_by(
                WorkspaceRecord.is_default.desc(), WorkspaceRecord.name
            )
        )
        return [self._to_domain(record) for record in result.scalars()]

    async def get(self, workspace_id: UUID) -> Workspace | None:
        record = await self._session.get(WorkspaceRecord, str(workspace_id))
        if record is None:
            return None
        return self._to_domain(record)

    async def get_default(self) -> Workspace | None:
        result = await self._session.execute(
            select(WorkspaceRecord)
            .where(WorkspaceRecord.is_default.is_(True))
            .order_by(WorkspaceRecord.created_at)
            .limit(1)
        )
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return self._to_domain(record)

    async def save(self, workspace: Workspace) -> Workspace:
        if workspace.is_default:
            await self._clear_default(except_id=workspace.id)
        record = await self._session.get(WorkspaceRecord, str(workspace.id))
        if record is None:
            self._session.add(self._to_record(workspace))
        else:
            self._update_record(record, workspace)
        await self._session.commit()
        return workspace

    async def set_default(self, workspace_id: UUID) -> Workspace | None:
        record = await self._session.get(WorkspaceRecord, str(workspace_id))
        if record is None:
            return None
        await self._clear_default(except_id=workspace_id)
        record.is_default = True
        record.active = True
        record.updated_at = datetime.now(UTC)
        await self._session.commit()
        return self._to_domain(record)

    async def delete(self, workspace_id: UUID) -> bool:
        record = await self._session.get(WorkspaceRecord, str(workspace_id))
        if record is None:
            return False
        await self._session.delete(record)
        await self._session.commit()
        return True

    async def _clear_default(self, except_id: UUID | None = None) -> None:
        statement = update(WorkspaceRecord).values(is_default=False)
        if except_id is not None:
            statement = statement.where(WorkspaceRecord.id != str(except_id))
        await self._session.execute(statement)

    def _to_record(self, workspace: Workspace) -> WorkspaceRecord:
        return WorkspaceRecord(
            id=str(workspace.id),
            name=workspace.name,
            description=workspace.description,
            active=workspace.active,
            is_default=workspace.is_default,
            created_at=workspace.audit.created_at,
            updated_at=workspace.audit.updated_at,
        )

    def _update_record(self, record: WorkspaceRecord, workspace: Workspace) -> None:
        record.name = workspace.name
        record.description = workspace.description
        record.active = workspace.active
        record.is_default = workspace.is_default
        record.created_at = workspace.audit.created_at
        record.updated_at = workspace.audit.updated_at

    def _to_domain(self, record: WorkspaceRecord) -> Workspace:
        return Workspace(
            id=UUID(record.id),
            name=record.name,
            description=record.description,
            active=record.active,
            is_default=record.is_default,
            audit=AuditInfo(
                created_at=_coerce_datetime(record.created_at),
                updated_at=_coerce_datetime(record.updated_at),
            ),
        )


def _coerce_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed
