from project_sentinel.domain.project import Project
from project_sentinel.domain.workspace import Workspace


def test_project_creation():
    ws = Workspace(name="Personal")

    project = Project(
        workspace_id=ws.id,
        name="Project Sentinel",
    )

    assert project.workspace_id == ws.id
    assert project.name == "Project Sentinel"


def test_project_default_description():
    ws = Workspace(name="Home")

    project = Project(
        workspace_id=ws.id,
        name="Home Tasks",
    )

    assert project.description == ""
    assert project.archived is False
