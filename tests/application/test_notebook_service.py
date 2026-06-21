import pytest
from toll.application.notebook_service import NotebookService
from toll.application.artifact_service import ArtifactService
from toll.core.feature_flags import FeatureFlags
from toll.ports.notebook import NotebookSource


@pytest.fixture
def nb_service(cm, tmp_path):
    import toll.core.config as cfg
    cfg.ARTIFACTS_PATH = tmp_path / "artifacts"
    cfg.ARCHIVE_PATH = cfg.ARTIFACTS_PATH / "archive"

    flags = FeatureFlags(cm=cm)
    flags.enable("notebooklm_enabled")
    flags.enable("notebooklm_strict_local")
    artifact_service = ArtifactService(cm)
    return NotebookService(artifact_service, cm, flags)


def test_create_notebook(nb_service):
    nb = nb_service.create_notebook(title="دفتر اختبار", description="وصف")
    assert nb.id
    assert nb.title == "دفتر اختبار"
    assert nb.description == "وصف"
    assert nb.source_count == 0
    assert nb.note_count == 0


def test_list_notebooks(nb_service):
    nb_service.create_notebook(title="دفتر 1")
    nb_service.create_notebook(title="دفتر 2")
    notebooks = nb_service.list_notebooks()
    assert len(notebooks) == 2
    assert notebooks[0].title == "دفتر 2"


def test_get_notebook(nb_service):
    created = nb_service.create_notebook(title="دفتر وحيد")
    found = nb_service.get_notebook(created.id)
    assert found is not None
    assert found.title == "دفتر وحيد"


def test_get_notebook_not_found(nb_service):
    assert nb_service.get_notebook("غير_موجود") is None


def test_update_notebook(nb_service):
    nb = nb_service.create_notebook(title="قبل")
    updated = nb_service.update_notebook(nb.id, title="بعد", description="وصف جديد")
    assert updated is not None
    assert updated.title == "بعد"
    assert updated.description == "وصف جديد"


def test_update_notebook_not_found(nb_service):
    assert nb_service.update_notebook("غير_موجود", title="اختبار") is None


def test_delete_notebook(nb_service):
    nb = nb_service.create_notebook(title="سيتم حذفه")
    assert nb_service.delete_notebook(nb.id) is True
    assert nb_service.get_notebook(nb.id) is None


def test_upload_source_persists_content(nb_service):
    nb = nb_service.create_notebook(title="مصدر")
    source = nb_service.upload_source(
        notebook_id=nb.id,
        content="هذا هو محتوى المصدر الذي يجب حفظه في قاعدة البيانات",
        file_name="test.txt",
        title="مصدر اختبار",
    )
    assert source is not None
    assert source.content == ""
    retrieved = nb_service._get_source_content(source.id)
    assert retrieved == "هذا هو محتوى المصدر الذي يجب حفظه في قاعدة البيانات"


def test_upload_source_not_found(nb_service):
    source = nb_service.upload_source(
        notebook_id="غير_موجود",
        content="محتوى",
        file_name="test.txt",
    )
    assert source is None


def test_list_sources(nb_service):
    nb = nb_service.create_notebook(title="مصادر متعددة")
    nb_service.upload_source(nb.id, "محتوى 1", "a.txt")
    nb_service.upload_source(nb.id, "محتوى 2", "b.txt")
    sources = nb_service.list_sources(nb.id)
    assert len(sources) == 2


def test_delete_source_returns_false_on_missing(nb_service):
    nb = nb_service.create_notebook(title="حذف مصدر")
    result = nb_service.delete_source(nb.id, "مصدر_غير_موجود")
    assert result is False


def test_delete_source_removes_source(nb_service):
    nb = nb_service.create_notebook(title="حذف مصدر موجود")
    source = nb_service.upload_source(nb.id, "محتوى", "test.txt")
    result = nb_service.delete_source(nb.id, source.id)
    assert result is True
    assert nb_service.list_sources(nb.id) == []


def test_create_notes_returns_empty_for_missing_notebook(nb_service):
    notes = nb_service.create_notes("غير_موجود")
    assert notes == []


def test_create_notes_returns_empty_with_no_sources(nb_service):
    nb = nb_service.create_notebook(title="دفتر فارغ")
    notes = nb_service.create_notes(nb.id)
    assert notes == []


def test_delete_note_returns_false_on_missing(nb_service):
    nb = nb_service.create_notebook(title="حذف ملاحظة")
    result = nb_service.delete_note(nb.id, "ملاحظة_غير_موجودة")
    assert result is False


def test_delete_snapshot_returns_false_on_missing(nb_service):
    nb = nb_service.create_notebook(title="حذف لقطة")
    result = nb_service.delete_snapshot(nb.id, "لقطة_غير_موجودة")
    assert result is False


def test_list_notes(nb_service):
    nb = nb_service.create_notebook(title="ملاحظات")
    notes = nb_service.list_notes(nb.id)
    assert notes == []


def test_create_snapshot(nb_service):
    flags = FeatureFlags(cm=nb_service.cm)
    flags.enable("notebooklm_snapshots")
    nb = nb_service.create_notebook(title="لقطة")
    snapshot = nb_service.create_snapshot(nb.id, label="لقطة اختبار")
    assert snapshot is not None
    assert snapshot.label == "لقطة اختبار"
    assert snapshot.source_count == 0
    assert snapshot.note_count == 0


def test_query_returns_empty_for_missing_notebook(nb_service):
    answer = nb_service.query("غير_موجود", "سؤال")
    assert answer == ""


def test_query_returns_empty_source_message(nb_service):
    nb = nb_service.create_notebook(title="دفتر بلا مصادر")
    answer = nb_service.query(nb.id, "سؤال")
    assert "لا توجد مصادر" in answer
