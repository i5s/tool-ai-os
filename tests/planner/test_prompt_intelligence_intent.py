from toll.planner.planner import Planner


def test_planner_has_prompt_intelligence_intent():
    p = Planner()
    assert "prompt_intelligence" in p.MATRIX
    assert "prompt_intelligence" in p.KEYWORDS


def test_planner_detects_prompt_intelligence_keyword():
    p = Planner()
    plan = p.plan("prompt enhance")
    assert plan.intent == "prompt_intelligence"


def test_planner_detects_arabic_keyword():
    p = Planner()
    plan = p.plan("تحسين البرومبت")
    assert plan.intent == "prompt_intelligence"


def test_planner_prompt_intelligence_is_auto():
    p = Planner()
    from toll.planner.planner import ApprovalLevel
    assert p.MATRIX["prompt_intelligence"] == ApprovalLevel.AUTO
