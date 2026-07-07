from uuid import UUID

from pydantic import Field

from project_sentinel.domain.common import Entity


class Project(Entity):
    """
    A project groups related tasks.

    Every project belongs to exactly one workspace.
    """

    workspace_id: UUID

    name: str = Field(min_length=1, max_length=100)

    description: str = Field(default="", max_length=1000)

    archived: bool = False
