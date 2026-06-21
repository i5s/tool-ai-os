import pytest
from toll.workflow.engine import WorkflowEngine
from toll.application.handler_registry import register_handlers


def test_register_handlers_creates_registrations(cm):
    wf = WorkflowEngine(cm=cm)
    register_handlers(wf, cm)
    assert "carousel" in wf._handlers
    assert "report" in wf._handlers
    assert "presentation" in wf._handlers
