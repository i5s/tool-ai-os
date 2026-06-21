import pytest
from toll.context.engine import ContextEngine
from toll.core.storage import Storage
from toll.memory.graph import MemoryGraph
from toll.workspace.manager import WorkspaceManager


@pytest.fixture
def context_engine(storage: Storage):
    return ContextEngine(storage=storage)


def test_build_context_includes_workspace_and_memories(context_engine):
    # Create workspace context
    ws = context_engine.workspace
    brand = ws.create_workspace("brand", "Test Brand")
    ws.set_active(brand_id=brand["id"])

    # Store a memory
    context_engine.memory.store(
        "brand", "tone", "professional", entity_id=brand["id"], importance_score=8
    )

    result = context_engine.build("What is our brand tone?")

    assert result.active_workspace["brand"]["name"] == "Test Brand"
    assert len(result.memories) == 1
    assert result.memories[0]["value"] == "professional"
    assert "Workspace Context" in result.prompt
    assert "Relevant Memories" in result.prompt
    assert "Current Message" in result.prompt


def test_build_context_with_recent_messages(context_engine):
    recent = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ]
    result = context_engine.build("How are you?", recent_messages=recent)

    assert len(result.recent_messages) == 2
    assert "Recent Conversation" in result.prompt
    assert "user: Hello" in result.prompt


def test_build_context_limits_memories(context_engine):
    ws = context_engine.workspace
    brand = ws.create_workspace("brand", "Many Memories")
    ws.set_active(brand_id=brand["id"])

    for i in range(15):
        context_engine.memory.store(
            "brand", f"key-{i}", f"value-{i}", entity_id=brand["id"]
        )

    result = context_engine.build("List all memories", memory_limit=5)
    assert len(result.memories) == 5
