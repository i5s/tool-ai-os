import pytest
from toll.core.conversations import ConversationStore
from toll.core.storage import Storage


@pytest.fixture
def store(storage: Storage):
    return ConversationStore(storage=storage)


def test_create_conversation(store):
    conv = store.create(title="Test Chat")
    assert conv["title"] == "Test Chat"
    assert conv["id"]
    assert conv["messages"] == []


def test_get_conversation(store):
    conv = store.create()
    found = store.get(conv["id"])
    assert found["id"] == conv["id"]


def test_list_conversations(store):
    store.create(title="A")
    store.create(title="B")
    convs = store.list()
    assert len(convs) == 2


def test_add_and_list_messages(store):
    conv = store.create()
    store.add_message(conv["id"], "user", "Hello")
    store.add_message(conv["id"], "assistant", "Hi there")

    messages = store.list_messages(conv["id"])
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_add_message_updates_conversation_timestamp(store):
    conv = store.create()
    original_updated = conv["updated_at"]
    store.add_message(conv["id"], "user", "Hello")
    updated = store.get(conv["id"])
    assert updated["updated_at"] > original_updated


def test_invalid_role(store):
    conv = store.create()
    with pytest.raises(ValueError):
        store.add_message(conv["id"], "bot", "Hello")


def test_update_title(store):
    conv = store.create(title="Old")
    store.update_title(conv["id"], "New")
    updated = store.get(conv["id"])
    assert updated["title"] == "New"


def test_delete_conversation(store):
    conv = store.create()
    store.add_message(conv["id"], "user", "Hi")
    assert store.delete(conv["id"]) is True
    assert store.get(conv["id"]) is None


def test_workspace_filter(store):
    brand_conv = store.create(title="Brand Chat", workspace_type="brand", workspace_id="b1")
    other_conv = store.create(title="Other")

    results = store.list(workspace_type="brand", workspace_id="b1")
    assert len(results) == 1
    assert results[0]["id"] == brand_conv["id"]
