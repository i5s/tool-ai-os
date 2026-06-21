import pytest
from toll.model_registry.service import ModelRegistryService


def test_service_init_seeds_data(cm, feature_flags):
    feature_flags.enable("model_registry_seed")
    svc = ModelRegistryService(cm=cm, flags=feature_flags)
    models = svc.list()
    assert len(models) >= 3


def test_register_new_model(cm, feature_flags):
    svc = ModelRegistryService(cm=cm, flags=feature_flags)
    m = svc.register({
        "provider": "replicate",
        "provider_model_id": "new-model",
        "name": "New Model",
        "media_types": ["image"],
        "tags": ["test"],
    })
    assert m.id == "replicate:new-model"
    assert m.name == "New Model"


def test_register_duplicate_raises(cm, feature_flags):
    svc = ModelRegistryService(cm=cm, flags=feature_flags)
    svc.register({
        "provider": "replicate", "provider_model_id": "dup", "name": "First",
    })
    with pytest.raises(ValueError, match="already exists"):
        svc.register({
            "provider": "replicate", "provider_model_id": "dup", "name": "Second",
        })


def test_get_model(cm, feature_flags):
    svc = ModelRegistryService(cm=cm, flags=feature_flags)
    svc.register({"provider": "r", "provider_model_id": "m1", "name": "M1"})
    m = svc.get("r:m1")
    assert m is not None
    assert m.name == "M1"


def test_get_missing(cm, feature_flags):
    svc = ModelRegistryService(cm=cm, flags=feature_flags)
    assert svc.get("nonexistent") is None


def test_list_filters(cm, feature_flags):
    svc = ModelRegistryService(cm=cm, flags=feature_flags)
    svc.register({"provider": "r", "provider_model_id": "a", "name": "A"})
    svc.register({"provider": "o", "provider_model_id": "b", "name": "B"})
    results = svc.list(provider="r")
    assert len(results) == 1


def test_disable_model(cm, feature_flags):
    svc = ModelRegistryService(cm=cm, flags=feature_flags)
    svc.register({"provider": "r", "provider_model_id": "d", "name": "D"})
    assert svc.disable("r:d")
    m = svc.get("r:d")
    assert m.status == "disabled"


def test_find_best_active(cm, feature_flags):
    svc = ModelRegistryService(cm=cm, flags=feature_flags)
    svc.register({"provider": "r", "provider_model_id": "a", "name": "A"})
    best = svc.find_best(media_type="image")
    assert best is not None
    assert best.status == "active"


def test_find_best_no_match(cm, feature_flags):
    svc = ModelRegistryService(cm=cm, flags=feature_flags)
    best = svc.find_best(media_type="video")
    assert best is None


def test_list_providers(cm, feature_flags):
    svc = ModelRegistryService(cm=cm, flags=feature_flags)
    svc.register({"provider": "r", "provider_model_id": "a", "name": "A"})
    svc.register({"provider": "o", "provider_model_id": "b", "name": "B"})
    providers = svc.list_providers()
    assert "r" in providers
    assert "o" in providers


def test_register_handler(cm, feature_flags):
    svc = ModelRegistryService(cm=cm, flags=feature_flags)
    result = svc.register_handler({
        "provider": "replicate", "provider_model_id": "flux-test", "name": "Flux Test",
    })
    assert "model" in result
    assert result["model"].id == "replicate:flux-test"


def test_list_handler(cm, feature_flags):
    svc = ModelRegistryService(cm=cm, flags=feature_flags)
    svc.register({"provider": "r", "provider_model_id": "a", "name": "A"})
    svc.register({"provider": "o", "provider_model_id": "b", "name": "B"})
    result = svc.list_handler({})
    assert result["total"] >= 2
