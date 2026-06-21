from toll.operations.cost_service import CostService


def test_total_empty(cm):
    svc = CostService(cm)
    result = svc.total()
    assert "total_cost_cents" in result
    assert "total_requests" in result


def test_by_provider_empty(cm):
    svc = CostService(cm)
    result = svc.by_provider()
    assert isinstance(result, list)


def test_by_model_empty(cm):
    svc = CostService(cm)
    result = svc.by_model()
    assert isinstance(result, list)


def test_daily_empty(cm):
    svc = CostService(cm)
    result = svc.daily()
    assert isinstance(result, list)
