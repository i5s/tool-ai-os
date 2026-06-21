import pytest
from toll.workspace.manager import WorkspaceManager
from toll.core.connection_manager import ConnectionManager


@pytest.fixture
def manager(cm: ConnectionManager):
    return WorkspaceManager(cm=cm, user_id="test-user")


def test_create_and_list_workspaces(manager):
    brand = manager.create_workspace("brand", "My Brand")
    uni = manager.create_workspace("university", "KU")
    project = manager.create_workspace("project", "Website")

    workspaces = manager.list_workspaces()
    assert len(workspaces) == 3
    assert {w["name"] for w in workspaces} == {"My Brand", "KU", "Website"}


def test_invalid_workspace_type(manager):
    with pytest.raises(ValueError):
        manager.create_workspace("team", "Bad")


def test_semester_lifecycle(manager):
    uni = manager.create_workspace("university", "KU")
    semester = manager.create_semester(uni["id"], "Fall 2025")

    assert semester["university_id"] == uni["id"]
    assert semester["name"] == "Fall 2025"

    semesters = manager.list_semesters(uni["id"])
    assert len(semesters) == 1


def test_semester_requires_university(manager):
    with pytest.raises(ValueError):
        manager.create_semester("invalid-id", "Fall 2025")


def test_active_workspace_state(manager):
    brand = manager.create_workspace("brand", "B")
    uni = manager.create_workspace("university", "U")
    project = manager.create_workspace("project", "P")

    state = manager.set_active(
        brand_id=brand["id"],
        university_id=uni["id"],
        project_id=project["id"],
    )

    assert state.active_brand_id == brand["id"]
    assert state.active_university_id == uni["id"]
    assert state.active_project_id == project["id"]

    active = manager.get_active()
    assert active.active_brand_id == brand["id"]

    summary = manager.get_active_summary()
    assert summary["brand"]["name"] == "B"
    assert summary["university"]["name"] == "U"


def test_active_workspace_partial_update(manager):
    brand = manager.create_workspace("brand", "B")
    manager.set_active(brand_id=brand["id"])

    project = manager.create_workspace("project", "P")
    state = manager.set_active(project_id=project["id"])

    assert state.active_brand_id == brand["id"]
    assert state.active_project_id == project["id"]


def test_clear_active_workspace(manager):
    brand = manager.create_workspace("brand", "B")
    manager.set_active(brand_id=brand["id"])
    manager.clear_active()

    assert manager.get_active().active_brand_id is None
