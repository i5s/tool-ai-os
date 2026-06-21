from toll.ports.model_registry import Model


def test_model_defaults():
    m = Model(id="r:f", provider="replicate", provider_model_id="f", name="Flux")
    assert m.status == "active"
    assert m.media_types == ["image"]
    assert m.capabilities == {}
    assert m.tags == []


def_model = Model(id="r:s", provider="replicate", provider_model_id="s", name="SDXL")


def test_model_with_cost():
    m = Model(
        id="r:f", provider="replicate", provider_model_id="f",
        name="Flux", cost_per_unit=0.002, cost_unit="per_image",
        tags=["fast", "general"],
    )
    assert m.cost_per_unit == 0.002
    assert "fast" in m.tags
