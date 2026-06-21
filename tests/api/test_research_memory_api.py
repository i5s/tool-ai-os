import pytest
from fastapi.testclient import TestClient
from api.main import app
from toll.core.connection_manager import ConnectionManager
from toll.application.research_service import ResearchService
from toll.application.artifact_service import ArtifactService
from toll.core.provider_selector import ProviderSelector
from toll.core.registry import ProviderRegistry
from toll.core.settings import Settings
from toll.core.feature_flags import FeatureFlags
from toll.research.memory_service import ResearchMemoryService
from toll.model.artifact import Artifact, ArtifactType, ArtifactStatus
from toll.ports.research_source import ResearchSource


def _ensure_tables(cm):
    cm.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            entity_id TEXT,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            importance_score INTEGER NOT NULL DEFAULT 5,
            source TEXT NOT NULL DEFAULT 'unknown',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_accessed_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    cm.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_memories_unique
        ON memories(type, entity_id, key)
    """)
    cm.execute("""
        CREATE TABLE IF NOT EXISTS research_memory_meta (
            memory_id TEXT PRIMARY KEY,
            artifact_id TEXT,
            source_id TEXT,
            topic TEXT NOT NULL,
            keywords TEXT NOT NULL DEFAULT '[]',
            times_accessed INTEGER DEFAULT 0,
            times_retopic_hit INTEGER DEFAULT 0,
            last_boosted_at TEXT,
            created_at TEXT NOT NULL
        )
    """)
    cm.execute("CREATE INDEX IF NOT EXISTS idx_research_memory_topic ON research_memory_meta(topic)")
    cm.commit()


def test_research_execute_indexes_memory(cm):
    _ensure_tables(cm)
    flags = FeatureFlags(cm=cm)
    flags.enable("research_memory_auto_index")
    flags.enable("research_provider")

    settings = Settings(cm=cm)
    registry = ProviderRegistry(settings)
    selector = ProviderSelector(registry, settings, flags)
    artifact_svc = ArtifactService(cm)
    svc = ResearchService(artifact_svc, selector, cm, flags)

    cm.execute(
        "INSERT OR IGNORE INTO workflows (id, plan, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        ("wf_mem_test", "{}", "pending", "2026-01-01T00:00:00", "2026-01-01T00:00:00"),
    )
    cm.commit()

    plan = {
        "title": "Memory Test Topic",
        "style": "apa",
        "max_sources": 1,
    }
    metadata = {
        "workflow_id": "wf_mem_test",
        "conversation_id": "conv_mem_test",
    }

    result = svc.execute(plan, metadata)
    assert "artifact_id" in result

    rms = ResearchMemoryService(cm=cm)
    memories = rms.memory.query(type="global")
    topic_memories = [m for m in memories if "research:topic:" in m.key]
    assert len(topic_memories) >= 1
    global_mem = topic_memories[0]
    assert "artifact_id" in global_mem.value


def test_context_includes_research_memory(cm):
    _ensure_tables(cm)
    flags = FeatureFlags(cm=cm)
    flags.enable("research_memory_context")

    from toll.context.engine import ContextEngine
    from toll.workspace.manager import WorkspaceManager

    engine = ContextEngine(cm=cm, flags=flags)

    rms = ResearchMemoryService(cm=cm)
    rms.memory.store(
        type="global",
        key="research:topic:ai safety",
        value={"summary": "AI safety research findings."},
        importance_score=8,
        source="research",
    )

    result = engine.build("Tell me about AI safety", memory_limit=10)
    assert "AI safety research findings" in result.prompt


def test_context_excludes_research_memory_when_flagged_off(cm):
    _ensure_tables(cm)
    flags = FeatureFlags(cm=cm)
    flags.disable("research_memory_context")

    from toll.context.engine import ContextEngine

    engine = ContextEngine(cm=cm, flags=flags)

    rms = ResearchMemoryService(cm=cm)
    rms.memory.store(
        type="global",
        key="research:topic:hidden topic",
        value={"summary": "This should not appear."},
        importance_score=8,
        source="research",
    )

    result = engine.build("Tell me about hidden topic", memory_limit=10)
    assert "research:topic:hidden topic" in result.prompt


def test_research_memory_persists_across_service_instances(cm):
    _ensure_tables(cm)
    flags = FeatureFlags(cm=cm)
    flags.enable("research_memory_auto_index")

    source = ResearchSource(
        title="Persistence Test",
        relevance_score=0.9,
        confidence_score=0.8,
        citation_count=50,
        source_type="journal",
        provider="test",
    )

    rms1 = ResearchMemoryService(cm=cm)
    rms1.index_source(source, artifact_id="art_persist")

    rms2 = ResearchMemoryService(cm=cm)
    memories = rms2.memory.query(type="knowledge")
    assert len(memories) >= 1
    assert any("research:source:" in m.key for m in memories)
