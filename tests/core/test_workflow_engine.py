import pytest
from toll.workflow.engine import WorkflowEngine, WorkflowStatus
from toll.core.storage import Storage


@pytest.fixture
def workflow_engine(storage: Storage):
    return WorkflowEngine(storage=storage)


def test_create_workflow_auto_execute(workflow_engine):
    plan = {
        "intent": "question",
        "level": "auto_execute",
        "can_auto_execute": True,
        "requires_approval": False,
        "plan_only": False,
        "title": "Question",
        "description": "Safe to execute",
        "steps": [],
        "metadata": {},
    }
    workflow = workflow_engine.create(plan)
    assert workflow.status == WorkflowStatus.APPROVED


def test_create_workflow_requires_approval(workflow_engine):
    plan = {
        "intent": "report",
        "level": "requires_approval",
        "can_auto_execute": False,
        "requires_approval": True,
        "plan_only": False,
        "title": "Report",
        "description": "Needs approval",
        "steps": [],
        "metadata": {},
    }
    workflow = workflow_engine.create(plan)
    assert workflow.status == WorkflowStatus.PENDING


def test_approve_and_run_workflow(workflow_engine):
    plan = {
        "intent": "report",
        "level": "requires_approval",
        "can_auto_execute": False,
        "requires_approval": True,
        "plan_only": False,
        "title": "Report",
        "description": "Needs approval",
        "steps": [],
        "metadata": {},
    }
    workflow = workflow_engine.create(plan)
    workflow_engine.register_handler("report", lambda p, m: {"executed": True})

    workflow_engine.approve(workflow.id)
    result = workflow_engine.run(workflow.id)

    assert result.status == WorkflowStatus.COMPLETED
    assert result.result == {"executed": True}


def test_reject_workflow(workflow_engine):
    plan = {
        "intent": "report",
        "level": "requires_approval",
        "can_auto_execute": False,
        "requires_approval": True,
        "plan_only": False,
        "title": "Report",
        "description": "Needs approval",
        "steps": [],
        "metadata": {},
    }
    workflow = workflow_engine.create(plan)
    workflow_engine.reject(workflow.id, "User rejected")

    updated = workflow_engine.get(workflow.id)
    assert updated.status == WorkflowStatus.REJECTED
    assert updated.error == "User rejected"


def test_run_without_approval_fails(workflow_engine):
    plan = {
        "intent": "report",
        "level": "requires_approval",
        "can_auto_execute": False,
        "requires_approval": True,
        "plan_only": False,
        "title": "Report",
        "description": "Needs approval",
        "steps": [],
        "metadata": {},
    }
    workflow = workflow_engine.create(plan)
    with pytest.raises(ValueError):
        workflow_engine.run(workflow.id)


def test_list_workflows_by_status(workflow_engine):
    plan = {
        "intent": "question",
        "level": "auto_execute",
        "can_auto_execute": True,
        "requires_approval": False,
        "plan_only": False,
        "title": "Question",
        "description": "Safe",
        "steps": [],
        "metadata": {},
    }
    workflow_engine.create(plan)

    approved = workflow_engine.list(status=WorkflowStatus.APPROVED)
    assert len(approved) == 1

    pending = workflow_engine.list(status=WorkflowStatus.PENDING)
    assert len(pending) == 0
