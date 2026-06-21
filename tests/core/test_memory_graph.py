import pytest
from toll.memory.graph import MemoryGraph
from toll.core.storage import Storage


@pytest.fixture
def graph(storage: Storage):
    return MemoryGraph(storage=storage)


def test_store_and_retrieve_memory(graph):
    mem = graph.store("global", "greeting", "hello", importance_score=7, source="test")
    assert mem.key == "greeting"
    assert mem.value == "hello"
    assert mem.importance_score == 7
    assert mem.source == "test"

    found = graph.get("global", "greeting")
    assert found is not None
    assert found.value == "hello"


def test_update_existing_memory(graph):
    graph.store("global", "counter", 1)
    mem = graph.store("global", "counter", 2)
    assert mem.value == 2

    rows = graph.query(type="global", key_prefix="counter")
    assert len(rows) == 1


def test_json_value_serialization(graph):
    data = {"tags": ["ai", "local"], "score": 9.5}
    mem = graph.store("knowledge", "config", data)
    assert mem.value == data


def test_workspace_retrieval(graph):
    brand_id = "brand-123"
    project_id = "project-456"
    graph.store("global", "all", "yes")
    graph.store("brand", "tone", "professional", entity_id=brand_id, importance_score=9)
    graph.store("project", "stack", "python", entity_id=project_id, importance_score=6)
    graph.store("university", "course", "cs101", entity_id="other-uni")

    results = graph.retrieve(brand_id=brand_id, project_id=project_id)
    keys = {m.key for m in results}
    assert "all" in keys
    assert "tone" in keys
    assert "stack" in keys
    assert "course" not in keys


def test_importance_adjustment_and_feedback(graph):
    mem = graph.store("global", "tip", "save often", importance_score=5)
    graph.adjust_importance(mem.id, 3)
    updated = graph.get_by_id(mem.id)
    assert updated.importance_score == 8

    graph.learn_from_feedback("global", "tip", None, approved=False)
    updated = graph.get("global", "tip")
    assert updated.importance_score == 7


def test_delete_memory(graph):
    mem = graph.store("global", "temp", "value")
    assert graph.delete(mem.id) is True
    assert graph.get_by_id(mem.id) is None
