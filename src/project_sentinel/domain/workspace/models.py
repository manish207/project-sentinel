from pydantic import Field

from project_sentinel.domain.common import Entity


class Workspace(Entity):
    """
    Top-level container for all user data.

    Every Project belongs to a Workspace.
    """

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    active: bool = True
