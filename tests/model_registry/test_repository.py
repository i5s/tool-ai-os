from toll.model_registry.repository import ModelRepository
from toll.ports.model_registry import Model


def _make_model(**kw):
    defaults = dict(id="r:test", provider="replicate", provider_model_id="test", name="Test")
    defaults.update(kw)
    return Model(**defaults)


def test_create_and_get(cm):
    repo = ModelRepository(cm)
    m = _make_model()
    repo.create(m)
    got = repo.get("r:test")
    assert got is not None
    assert got.name == "Test"
    assert got.provider == "replicate"


def test_get_missing(cm):
    repo = ModelRepository(cm)
    assert repo.get("nonexistent") is None


def test_get_by_provider(cm):
    repo = ModelRepository(cm)
    repo.create(_make_model())
    got = repo.get_by_provider("replicate", "test")
    assert got is not None
    assert got.id == "r:test"


def test_list_filters_by_provider(cm):
    repo = ModelRepository(cm)
    repo.create(_make_model(id="r:a", provider="replicate"))
    repo.create(_make_model(id="o:a", provider="openai", provider_model_id="a"))
    results = repo.list(provider="replicate")
    assert len(results) == 1
    assert results[0].provider == "replicate"


def test_list_filters_by_status(cm):
    repo = ModelRepository(cm)
    repo.create(_make_model(id="r:a", status="active"))
    repo.create(_make_model(id="r:b", status="disabled", provider_model_id="b"))
    active = repo.list(status="active")
    assert len(active) == 1


def test_list_filters_by_media_type(cm):
    repo = ModelRepository(cm)
    repo.create(_make_model(id="r:a", media_types=["image"]))
    video = repo.list(media_type="video")
    assert len(video) == 0


def test_update_model(cm):
    repo = ModelRepository(cm)
    repo.create(_make_model())
    repo.update("r:test", {"name": "Updated", "cost_per_unit": 0.5})
    got = repo.get("r:test")
    assert got.name == "Updated"
    assert got.cost_per_unit == 0.5


def test_disable_model(cm):
    repo = ModelRepository(cm)
    repo.create(_make_model())
    assert repo.disable("r:test")
    got = repo.get("r:test")
    assert got.status == "disabled"


def test_list_providers(cm):
    repo = ModelRepository(cm)
    repo.create(_make_model(id="r:a", provider="replicate"))
    repo.create(_make_model(id="o:a", provider="openai", provider_model_id="a"))
    providers = repo.list_providers()
    assert "replicate" in providers
    assert "openai" in providers
