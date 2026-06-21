from toll.prompt.profile_service import ExecutionProfileService, PromptProfileService


def test_execution_list():
    svc = ExecutionProfileService()
    result = svc.list()
    assert result["success"] is True
    assert len(result["profiles"]) == 6


def test_execution_get():
    svc = ExecutionProfileService()
    result = svc.get("marketing")
    assert result["success"] is True
    assert result["profile"]["name"] == "Marketing Profile"


def test_execution_get_missing():
    svc = ExecutionProfileService()
    result = svc.get("nonexistent")
    assert result["success"] is False


def test_create_profile(cm, feature_flags):
    svc = PromptProfileService(cm, feature_flags)
    result = svc.create({"name": "Custom Profile", "template": "Show {subject}"})
    assert result["success"] is True
    assert result["profile"]["name"] == "Custom Profile"


def test_create_profile_no_name(cm, feature_flags):
    svc = PromptProfileService(cm, feature_flags)
    result = svc.create({"name": ""})
    assert result["success"] is False
    assert "name" in result["error"]


def test_get_profile(cm, feature_flags):
    svc = PromptProfileService(cm, feature_flags)
    svc.create({"id": "t:get", "name": "Get Test"})
    result = svc.get("t:get")
    assert result["success"] is True
    assert result["profile"]["name"] == "Get Test"


def test_get_missing(cm, feature_flags):
    svc = PromptProfileService(cm, feature_flags)
    result = svc.get("nonexistent")
    assert result["success"] is False


def test_list_profiles(cm, feature_flags):
    svc = PromptProfileService(cm, feature_flags)
    svc.create({"name": "A", "media_types": ["image"]})
    svc.create({"name": "B", "media_types": ["text"]})
    result = svc.list()
    assert result["success"] is True
    assert result["total"] >= 2


def test_update_profile(cm, feature_flags):
    svc = PromptProfileService(cm, feature_flags)
    svc.create({"id": "t:upd", "name": "Original"})
    result = svc.update("t:upd", {"name": "Updated"})
    assert result["success"] is True
    assert result["profile"]["version"] >= 2


def test_update_missing(cm, feature_flags):
    svc = PromptProfileService(cm, feature_flags)
    result = svc.update("nonexistent", {"name": "X"})
    assert result["success"] is False


def test_delete_profile(cm, feature_flags):
    svc = PromptProfileService(cm, feature_flags)
    svc.create({"id": "t:del", "name": "Delete"})
    result = svc.delete("t:del")
    assert result["success"] is True
    assert svc.get("t:del")["success"] is False


def test_get_version_history(cm, feature_flags):
    svc = PromptProfileService(cm, feature_flags)
    svc.create({"id": "t:hist", "name": "V1"})
    svc.update("t:hist", {"name": "V2"})
    result = svc.get_version_history("t:hist")
    assert result["success"] is True
    assert len(result["versions"]) >= 1
