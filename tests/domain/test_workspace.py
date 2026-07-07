from project_sentinel.domain.workspace import Workspace


def test_workspace_creation():
    workspace = Workspace(name="Personal")

    assert workspace.name == "Personal"
    assert workspace.active is True


def test_workspace_description_default():
    workspace = Workspace(name="Home")

    assert workspace.description == ""
