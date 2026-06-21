import pytest
from toll.planner.planner import Planner, PlannerMode, ApprovalLevel


def test_question_is_auto_execute():
    planner = Planner()
    plan = planner.plan("What is AI?")
    assert plan.level == ApprovalLevel.AUTO
    assert plan.can_auto_execute is True


def test_report_requires_approval():
    planner = Planner()
    plan = planner.plan("Write a report about AI")
    assert plan.level == ApprovalLevel.APPROVAL
    assert plan.requires_approval is True


def test_research_plan_is_plan_only():
    planner = Planner()
    plan = planner.plan("Create a research plan for climate change")
    assert plan.level == ApprovalLevel.PLAN_ONLY
    assert plan.plan_only is True


def test_workspace_create_is_auto_execute():
    planner = Planner()
    plan = planner.plan("/brand New Brand")
    assert plan.intent == "workspace_create"
    assert plan.level == ApprovalLevel.AUTO


def test_workspace_delete_requires_approval():
    planner = Planner()
    plan = planner.plan("Delete workspace X")
    assert plan.intent == "workspace_delete"
    assert plan.level == ApprovalLevel.APPROVAL


def test_memory_suggest_is_auto_execute():
    planner = Planner()
    plan = planner.plan("Remember this: my favorite color is blue")
    assert plan.intent == "memory_suggest"
    assert plan.level == ApprovalLevel.AUTO


def test_memory_promote_requires_approval():
    planner = Planner()
    plan = planner.plan("Promote this memory to long-term")
    assert plan.intent == "memory_promote"
    assert plan.level == ApprovalLevel.APPROVAL


def test_strict_mode_escalates():
    planner = Planner(PlannerMode.STRICT)
    plan = planner.plan("What is AI?")
    # Questions remain auto in strict mode because they are read-only
    assert plan.level == ApprovalLevel.AUTO

    plan = planner.plan("Create a research plan for climate change")
    assert plan.level == ApprovalLevel.APPROVAL


def test_fast_mode_allows_plan_only_auto():
    planner = Planner(PlannerMode.FAST)
    plan = planner.plan("Create a research plan for climate change")
    assert plan.level == ApprovalLevel.AUTO

    # Approval-level actions still require approval even in fast mode
    plan = planner.plan("Write a report about AI")
    assert plan.level == ApprovalLevel.APPROVAL


def test_from_flags_strict():
    planner = Planner.from_flags(strict=True)
    assert planner.mode == PlannerMode.STRICT


def test_from_flags_fast():
    planner = Planner.from_flags(fast=True)
    assert planner.mode == PlannerMode.FAST


def test_from_flags_balanced_default():
    planner = Planner.from_flags()
    assert planner.mode == PlannerMode.BALANCED
