from toll.operations.storage_service import StorageService
from toll.model.artifact import Artifact, ArtifactRepository, ArtifactStatus, ArtifactType


def test_summary(cm):
    svc = StorageService(cm)
    result = svc.summary()
    assert "total_artifacts" in result
    assert "by_type" in result


def test_retention_policies_default(cm):
    svc = StorageService(cm)
    policies = svc.retention_policies()
    assert len(policies) >= 1
    assert policies[0]["name"] == "Default Policy"


def test_upsert_retention_policy(cm):
    svc = StorageService(cm)
    result = svc.upsert_retention_policy(
        name="Images Policy", retention_days=7,
        media_type="image",
    )
    assert result["retention_days"] == 7
    policies = svc.retention_policies()
    names = [p["name"] for p in policies]
    assert "Images Policy" in names


def test_delete_retention_policy(cm):
    svc = StorageService(cm)
    result = svc.upsert_retention_policy(name="Temp", retention_days=1)
    svc.delete_retention_policy(result["id"])
    policies = svc.retention_policies()
    assert all(p["name"] != "Temp" for p in policies)


def test_published_assets(cm):
    repo = ArtifactRepository(cm)
    art = repo.create(Artifact(
        id="pub:1", type=ArtifactType.REPORT,
        status=ArtifactStatus.COMPLETED, title="Published",
        rendered_path="/tmp/test.html",
    ))
    svc = StorageService(cm)
    assets = svc.published_assets()
    assert len(assets) >= 1


def test_pending_cleanup_empty(cm):
    svc = StorageService(cm)
    pending = svc.pending_cleanup(older_than_days=1)
    assert isinstance(pending, list)
