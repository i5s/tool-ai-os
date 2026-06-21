import pytest
from toll.workflow.engine import WorkflowEngine
from toll.application.handler_registry import register_handlers
from toll.core.feature_flags import FeatureFlags


def test_register_handlers_creates_registrations(cm):
    wf = WorkflowEngine(cm=cm)
    register_handlers(wf, cm)
    assert "carousel" in wf._handlers
    assert "report" in wf._handlers
    assert "presentation" in wf._handlers


def test_register_notebook_handlers_when_enabled(cm):
    flags = FeatureFlags(cm=cm)
    flags.enable("notebooklm_enabled")
    wf = WorkflowEngine(cm=cm)
    register_handlers(wf, cm)
    assert "notebook_upload" in wf._handlers
    assert "notebook_notes" in wf._handlers
    assert "notebook_query" in wf._handlers


def test_notebook_handlers_not_registered_when_disabled(cm):
    flags = FeatureFlags(cm=cm)
    flags.disable("notebooklm_enabled")
    wf = WorkflowEngine(cm=cm)
    register_handlers(wf, cm)
    assert "notebook_upload" not in wf._handlers
    assert "notebook_notes" not in wf._handlers
    assert "notebook_query" not in wf._handlers


def test_notebook_upload_handler_dispatches(cm):
    flags = FeatureFlags(cm=cm)
    flags.enable("notebooklm_enabled")
    wf = WorkflowEngine(cm=cm)
    register_handlers(wf, cm)
    import uuid
    from toll.application.notebook_service import NotebookService
    from toll.application.artifact_service import ArtifactService
    svc = NotebookService(ArtifactService(cm), cm, flags)
    nb = svc.create_notebook(title="دفتر دفع")
    plan = {
        "intent": "notebook_upload",
        "notebook_id": nb.id,
        "content": "محتوى عبر سير العمل",
        "file_name": "workflow.txt",
        "title": "عمل",
    }
    result = wf._handlers["notebook_upload"](plan, {"user_id": "test"})
    assert result is not None
    assert result.file_name == "workflow.txt"
