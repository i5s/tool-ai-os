import pytest
from toll.workflow.engine import WorkflowEngine, WorkflowStatus
from toll.core.connection_manager import ConnectionManager


@pytest.fixture
def wf_cm(cm: ConnectionManager):
    return cm


@pytest.fixture
def workflow_engine(wf_cm: ConnectionManager):
    return WorkflowEngine(cm=wf_cm)


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


def test_create_and_run_auto_executes(workflow_engine):
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
    workflow_engine.register_handler("question", lambda p, m: {"done": True})
    workflow = workflow_engine.create_and_run(plan)
    assert workflow.status == WorkflowStatus.COMPLETED
    assert workflow.result == {"done": True}


def test_create_and_run_pending_requires_approval(workflow_engine):
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
    workflow = workflow_engine.create_and_run(plan)
    # Pending workflows are not auto-run by create_and_run
    assert workflow.status == WorkflowStatus.PENDING


def test_recover_marks_running_as_failed(workflow_engine):
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
    wf = workflow_engine.create(plan)
    # Manually set to running to simulate interrupted execution
    wf.status = WorkflowStatus.RUNNING
    workflow_engine._persist(wf)

    recovered = workflow_engine.recover()
    assert len(recovered) == 1
    assert recovered[0].status == WorkflowStatus.FAILED
    assert "Server restart interrupted" in recovered[0].error

    # Verify it stays failed after second recover
    recovered2 = workflow_engine.recover()
    assert len(recovered2) == 0
