from toll.operations.cleanup_service import CleanupService


def test_simulate_empty(cm):
    svc = CleanupService(cm)
    result = svc.simulate()
    assert "total_artifacts" in result
    assert result["total_artifacts"] == 0


def test_simulate_with_policy(cm):
    svc = CleanupService(cm)
    result = svc.simulate()
    assert isinstance(result["by_policy"], list)


def test_execute_empty(cm):
    svc = CleanupService(cm)
    result = svc.execute()
    assert result["total_cleaned"] == 0


def test_log_empty(cm):
    svc = CleanupService(cm)
    entries = svc.log()
    assert entries == []


def test_default_policy_exists(cm):
    svc = CleanupService(cm)
    policies = svc._enabled_policies()
    assert len(policies) >= 1
    assert policies[0]["name"] == "Default Policy"
