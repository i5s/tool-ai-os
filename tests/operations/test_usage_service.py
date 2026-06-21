from toll.operations.usage_service import UsageService


def test_record_usage(cm):
    svc = UsageService(cm)
    svc.record(provider="opencode", media_type="text",
               model_id="big-pickle", duration_ms=1200)
    summary = svc.summary()
    assert summary["today"]["requests"] >= 1


def test_record_with_cost(cm):
    svc = UsageService(cm)
    svc.record(provider="replicate", media_type="image",
               model_id="flux", estimated_cost_cents=0.5)
    summary = svc.summary()
    assert summary["today"]["total_cost_cents"] >= 0.5


def test_record_failure(cm):
    svc = UsageService(cm)
    svc.record(provider="ollama", media_type="text", success=False,
               error="timeout")
    summary = svc.summary()
    assert summary["today"]["errors"] >= 1


def test_by_provider(cm):
    svc = UsageService(cm)
    svc.record(provider="p1", media_type="text")
    svc.record(provider="p2", media_type="text")
    result = svc.by_provider()
    providers = {p["provider"] for p in result}
    assert "p1" in providers
    assert "p2" in providers


def test_by_model(cm):
    svc = UsageService(cm)
    svc.record(provider="r", media_type="text", model_id="m1")
    svc.record(provider="r", media_type="text", model_id="m2")
    result = svc.by_model()
    models = {m["model_id"] for m in result}
    assert "m1" in models
    assert "m2" in models


def test_daily_cost(cm):
    svc = UsageService(cm)
    svc.record(provider="r", media_type="text", estimated_cost_cents=1.0)
    daily = svc.daily_cost()
    assert len(daily) >= 1
    assert daily[0]["total_cost_cents"] >= 1.0


def test_recent_entries(cm):
    svc = UsageService(cm)
    svc.record(provider="r", media_type="text")
    recent = svc.recent(limit=5)
    assert len(recent) >= 1
    assert recent[0]["provider"] == "r"


def test_summary_empty_db(cm):
    svc = UsageService(cm)
    summary = svc.summary()
    assert summary["today"]["requests"] == 0
    assert summary["today"]["total_cost_cents"] == 0.0
