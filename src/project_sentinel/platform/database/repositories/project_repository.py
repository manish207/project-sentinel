from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from project_sentinel.domain.common import AuditInfo
from project_sentinel.domain.project import Project
from project_sentinel.platform.database.models import ProjectRecord


class SqlAlchemyProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, project: Project) -> Project:
        self._session.add(self._to_record(project))
        await self._session.commit()
        return project

    async def list(self) -> list[Project]:
        result = await self._session.execute(
            select(ProjectRecord).order_by(ProjectRecord.name)
        )
        return [self._to_domain(record) for record in result.scalars()]

    async def get(self, project_id: UUID) -> Project | None:
        record = await self._session.get(ProjectRecord, str(project_id))
        if record is None:
            return None
        return self._to_domain(record)

    async def save(self, project: Project) -> Project:
        record = await self._session.get(ProjectRecord, str(project.id))
        if record is None:
            self._session.add(self._to_record(project))
        else:
            self._update_record(record, project)
        await self._session.commit()
        return project

    async def delete(self, project_id: UUID) -> bool:
        record = await self._session.get(ProjectRecord, str(project_id))
        if record is None:
            return False
        await self._session.delete(record)
        await self._session.commit()
        return True

    def _to_record(self, project: Project) -> ProjectRecord:
        return ProjectRecord(
            id=str(project.id),
            workspace_id=str(project.workspace_id),
            name=project.name,
            description=project.description,
            archived=project.archived,
            created_at=project.audit.created_at,
            updated_at=project.audit.updated_at,
        )

    def _update_record(self, record: ProjectRecord, project: Project) -> None:
        record.workspace_id = str(project.workspace_id)
        record.name = project.name
        record.description = project.description
        record.archived = project.archived
        record.created_at = project.audit.created_at
        record.updated_at = project.audit.updated_at

    def _to_domain(self, record: ProjectRecord) -> Project:
        return Project(
            id=UUID(record.id),
            workspace_id=UUID(record.workspace_id),
            name=record.name,
            description=record.description,
            archived=record.archived,
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
