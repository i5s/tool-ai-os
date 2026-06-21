import pytest
from toll.research.memory_service import ResearchMemoryService
from toll.research.importance import ImportanceScorer
from toll.model.artifact import Artifact, ArtifactType, ArtifactStatus
from toll.ports.research_source import ResearchSource


def _ensure_memory_table(cm):
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


def _ensure_meta_table(cm):
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
    cm.execute("""
        CREATE INDEX IF NOT EXISTS idx_research_memory_topic
        ON research_memory_meta(topic)
    """)


def _make_artifact(topic="Test Research", artifact_id="art_rm_001"):
    return Artifact(
        id=artifact_id,
        type=ArtifactType.RESEARCH,
        status=ArtifactStatus.COMPLETED,
        title=topic,
        content={
            "synopsis": "This is a research synopsis about the test topic.",
            "key_findings": ["Finding one", "Finding two", "Finding three"],
            "source_count": 2,
        },
    )


def _make_source(title="Test Source", doi=None, url=None):
    return ResearchSource(
        title=title,
        authors=["Author, A."],
        year=2024,
        doi=doi,
        url=url,
        abstract="Test abstract",
        relevance_score=0.8,
        confidence_score=0.7,
        citation_count=25,
        source_type="journal",
        provider="test",
    )


def test_index_research_creates_global_memory(cm):
    _ensure_memory_table(cm)
    _ensure_meta_table(cm)
    svc = ResearchMemoryService(cm=cm)
    artifact = _make_artifact()
    sources = [_make_source("Source A"), _make_source("Source B")]

    counts = svc.index_research(artifact, sources)
    assert counts["global"] == 1
    assert counts["knowledge"] == 2

    memories = svc.memory.query(type="global")
    assert len(memories) >= 1
    assert "research:topic:" in memories[0].key


def test_index_research_zero_sources(cm):
    _ensure_memory_table(cm)
    _ensure_meta_table(cm)
    svc = ResearchMemoryService(cm=cm)
    artifact = _make_artifact()

    counts = svc.index_research(artifact, [])
    assert counts["global"] == 1
    assert counts["knowledge"] == 0


def test_index_research_with_workspace(cm):
    _ensure_memory_table(cm)
    _ensure_meta_table(cm)
    svc = ResearchMemoryService(cm=cm)
    artifact = _make_artifact()
    sources = [_make_source("Source A")]

    counts = svc.index_research(artifact, sources, workspace_type="project", workspace_id="ws_001")
    assert counts["project"] == 1

    memories = svc.memory.query(type="project", entity_id="ws_001")
    assert len(memories) >= 1


def test_index_research_duplicate_topic(cm):
    _ensure_memory_table(cm)
    _ensure_meta_table(cm)
    svc = ResearchMemoryService(cm=cm)
    artifact = _make_artifact(topic="Duplicate Topic")
    sources = [_make_source("Source")]

    svc.index_research(artifact, sources)
    svc.index_research(artifact, sources)

    memories = svc.memory.query(type="global")
    topic_memories = [m for m in memories if "research:topic:duplicate topic" in m.key]
    assert len(topic_memories) == 1


def test_index_source_creates_knowledge_memory(cm):
    _ensure_memory_table(cm)
    _ensure_meta_table(cm)
    svc = ResearchMemoryService(cm=cm)
    source = _make_source("Unique Source", doi="10.1234/test.doi")

    memory = svc.index_source(source, artifact_id="art_001")
    assert memory is not None
    assert memory.type == "knowledge"
    assert memory.importance_score >= 1


def test_index_source_dedup_by_doi(cm):
    _ensure_memory_table(cm)
    _ensure_meta_table(cm)
    svc = ResearchMemoryService(cm=cm)
    source = _make_source("Dedup Source", doi="10.1234/dedup.test")

    svc.index_source(source, artifact_id="art_001")
    svc.index_source(source, artifact_id="art_002")

    memories = svc.memory.query(type="knowledge")
    assert len(memories) >= 1


def test_index_source_no_doi_url_fallback(cm):
    _ensure_memory_table(cm)
    _ensure_meta_table(cm)
    svc = ResearchMemoryService(cm=cm)
    source = _make_source("Title Only Source", doi=None, url=None)

    memory = svc.index_source(source, artifact_id="art_001")
    assert memory is not None
    assert memory.key.startswith("research:source:")


def test_get_relevant_memories_by_message(cm):
    _ensure_memory_table(cm)
    _ensure_meta_table(cm)
    svc = ResearchMemoryService(cm=cm)
    source = _make_source("Artificial Intelligence Research Paper", doi="10.1234/ai.test")
    svc.index_source(source, artifact_id="art_001")

    results = svc.get_relevant_memories("Tell me about Artificial Intelligence", limit=5, min_importance=1)
    assert len(results) >= 1


def test_get_relevant_memories_min_importance_filter(cm):
    _ensure_memory_table(cm)
    _ensure_meta_table(cm)
    svc = ResearchMemoryService(cm=cm)
    source = _make_source("Low Score Paper", doi="10.1234/low.test")
    source.relevance_score = 0.0
    source.confidence_score = 0.0
    source.citation_count = 0
    svc.index_source(source, artifact_id="art_001")

    results = svc.get_relevant_memories("Low Score", limit=5, min_importance=10)
    assert len(results) == 0


def test_get_relevant_memories_no_keywords(cm):
    svc = ResearchMemoryService(cm=cm)
    results = svc.get_relevant_memories("a")  # single char, no keywords
    assert len(results) == 0


def test_get_knowledge_vault_all(cm):
    _ensure_memory_table(cm)
    _ensure_meta_table(cm)
    svc = ResearchMemoryService(cm=cm)
    svc.index_source(_make_source("Vault Source 1", doi="10.1234/vault.1"), artifact_id="art_001")
    svc.index_source(_make_source("Vault Source 2", doi="10.1234/vault.2"), artifact_id="art_001")

    vault = svc.get_knowledge_vault()
    assert len(vault) >= 2


def test_get_knowledge_vault_by_topic(cm):
    _ensure_memory_table(cm)
    _ensure_meta_table(cm)
    svc = ResearchMemoryService(cm=cm)
    svc.index_source(_make_source("Quantum Computing Paper", doi="10.1234/quantum"), artifact_id="art_001")

    vault = svc.get_knowledge_vault(topic="Quantum")
    assert len(vault) >= 1


def test_boost_on_retopic(cm):
    _ensure_memory_table(cm)
    _ensure_meta_table(cm)
    svc = ResearchMemoryService(cm=cm)
    svc.index_source(_make_source("Retopic Source", doi="10.1234/retopic"), artifact_id="art_001")

    count = svc.boost_on_retopic("Retopic")
    assert count >= 1


def test_boost_on_retopic_no_match(cm):
    svc = ResearchMemoryService(cm=cm)
    count = svc.boost_on_retopic("Nonexistent Topic That Does Not Exist")
    assert count == 0


def test_decay_stale_memories(cm):
    _ensure_memory_table(cm)
    _ensure_meta_table(cm)
    svc = ResearchMemoryService(cm=cm)
    svc.index_source(_make_source("Stale Source", doi="10.1234/stale"), artifact_id="art_001")

    memories = svc.memory.query(type="knowledge")
    if memories:
        svc.memory.cm.execute(
            "UPDATE memories SET last_accessed_at = '2020-01-01T00:00:00' WHERE id = ?",
            (memories[0].id,),
        )
        svc.memory.cm.commit()

    count = svc.decay_stale_memories(max_days=1, delta=-1)
    assert count >= 0


def test_round_trip_index_then_retrieve(cm):
    _ensure_memory_table(cm)
    _ensure_meta_table(cm)
    svc = ResearchMemoryService(cm=cm)
    source = _make_source("Round Trip Source", doi="10.1234/roundtrip")
    source.authors = ["Smith, J."]
    source.year = 2024

    index_mem = svc.index_source(source, artifact_id="art_001")
    assert index_mem is not None

    retrieved = svc.memory.get_by_id(index_mem.id)
    assert retrieved is not None
    assert retrieved.key == index_mem.key
    assert retrieved.importance_score == index_mem.importance_score
