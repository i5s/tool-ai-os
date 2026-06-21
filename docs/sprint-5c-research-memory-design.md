# Sprint 5C: Research Memory Automation — Design Document

> Date: 2026-06-21
> Based on: Sprint 5B + 5B.2 architecture, MemoryGraph (graph.py), ContextEngine, DedupEngine, SourceManager

---

## 1. Problem Statement

Research outputs today are one-shot artifacts. They render as HTML, persist to SQLite, but have zero feedback into the system's long-term memory:

- `ResearchService.execute()` creates an Artifact with sources + synopsis + citations, then forgets everything
- `MemoryGraph` exists with 5 scopes (global, brand, university, project, knowledge) but receives no research data
- `ContextEngine.build()` queries `memory.retrieve()` but gets only manually-stored memories — no research signals
- Users repeat the same research topics because previous findings aren't surfaced

**Goal:** After every research execution, automatically extract and persist structured memories so that:
1. Future queries against the same workspace recall previous findings
2. The context engine auto-injects relevant research memories into prompts
3. Sources build up a long-term "knowledge vault" that crosses project boundaries
4. Importance scores auto-adjust based on usage patterns

**Constraints:**
- Local First, SQLite only
- No cloud dependencies, no RAG framework, no vector store, no embeddings
- No Media Layer, no Project Intelligence, no Agent Layer, no UI redesign

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       Existing Layer                             │
│  ┌──────────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │ ResearchService  │  │ NotebookService │  │ ContextEngine  │  │
│  │ - execute()      │  │ - query()       │  │ - build()      │  │
│  │ - execute_quick()│  │ - sync()        │  └──────┬─────────┘  │
│  └────────┬─────────┘  └────────┬───────┘         │             │
└───────────┼─────────────────────┼──────────────────┼─────────────┘
            │                     │                  │
            ▼                     ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Sprint 5C Layer                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              ResearchMemoryService                        │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐  │   │
│  │  │  Importance  │ │  Knowledge   │ │  Context Feed   │  │   │
│  │  │  Scorer     │ │  Vault       │ │  Research       │  │   │
│  │  └──────┬───────┘ └──────┬───────┘ └────────┬────────┘  │   │
│  └─────────┼────────────────┼──────────────────┼────────────┘   │
└────────────┼────────────────┼──────────────────┼────────────────┘
             │                │                  │
             ▼                ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Infrastructure                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
│  │ SQLite   │  │ Memory   │  │ Source   │  │ Research     │    │
│  │ (local)  │  │ Graph    │  │ Manager  │  │ Sources DB   │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **New service, not overloaded**: `ResearchMemoryService` is separate from `MemoryGraph` because it owns research-specific logic (importance calculation from source metadata, knowledge vault dedup, research→memory mapping). `MemoryGraph` remains the generic CRUD store.

2. **Memory types map to research semantics**:
   - `type='global'` → cross-cutting research findings (key facts, definitions)
   - `type='knowledge'` → per-source insights, stored with `entity_id=source_id`
   - `type='project'` → workspace-scoped research summaries
   - `type='brand'` → brand-specific research results

3. **Importance is computed, not guessed**: Every memory gets an initial importance score derived from `relevance_score * 0.4 + confidence_score * 0.3 + min(citation_count / 100, 1.0) * 0.3`, mapped to 1-10 scale. This is recalculated on source access.

4. **Knowledge Vault is a SQLite query, not a new store**: "Knowledge Vault" is `memories WHERE type='knowledge'` — no new table needed. The vault is the set of all knowledge-scope memories, optionally filtered by `key_prefix` for topic-based lookup.

5. **Context injection is opt-in**: Research memories appear in context only when a feature flag (`research_memory_context`) is enabled, and only for memories with `importance >= 4`. Low-importance memories don't clutter the prompt.

---

## 3. Data Flow

### 3.1 After Research Execution

```
ResearchService.execute()
        │
        ▼
┌─────────────────────────────────────┐
│ 1. Research completes as before     │
│    - collect sources                │
│    - synthesize                     │
│    - create artifact                │
│    - store sources                  │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ 2. ResearchMemoryService.index()    │
│    Called post-execute if flag      │
│    research_memory_auto_index=True  │
│                                     │
│    A. Extract key findings          │
│       → memories (global scope)     │
│    B. Index each source             │
│       → memories (knowledge scope)  │
│    C. Store research summary        │
│       → memory (project scope)      │
│    D. Tag with importance score     │
└─────────────────────────────────────┘
```

### 3.2 Before Context Build

```
ContextEngine.build(message, ...)
        │
        ▼
┌─────────────────────────────────────┐
│ 1. Normal context assembly:         │
│    - workspace state                │
│    - recent messages                │
│    - memories (existing)            │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ 2. NEW: Research memory injection   │
│    if flag research_memory_context  │
│    = True:                          │
│                                     │
│    ResearchMemoryService            │
│    .get_relevant_memories(message)  │
│                                     │
│    Returns top-K knowledge vault    │
│    memories matching the message    │
│    (key_prefix-based filtering)     │
│                                     │
│    These are appended to the        │
│    [Relevant Memories] block        │
└─────────────────────────────────────┘
```

### 3.3 Importance Feedback Loop

```
User views/uses research result
        │
        ▼
┌─────────────────────────────────────┐
│ MemoryGraph.touch(memory_id)        │
│ → updates last_accessed_at          │
│ → recency score increases           │
│ → memory ranks higher in retrieve() │
└─────────────────────────────────────┘

User re-queries same topic
        │
        ▼
┌─────────────────────────────────────┐
│ ResearchMemoryService               │
│ .boost_on_retopic(topic)            │
│ → finds memories with key_prefix    │
│   matching topic                    │
│ → calls adjust_importance(+1)       │
│ → topic gets importance boost       │
└─────────────────────────────────────┘

User ignores / dismisses finding
        │
        ▼
┌─────────────────────────────────────┐
│ ResearchMemoryService               │
│ .decay_on_ignore(topic)             │
│ → adjust_importance(-1)             │
│ → low-importance memories           │
│   eventually excluded from context  │
└─────────────────────────────────────┘
```

---

## 4. Service Design

### 4.1 ResearchMemoryService

```python
# toll/research/memory_service.py

class ResearchMemoryService:
    """Bridges research outputs into long-term MemoryGraph storage."""

    def __init__(self, cm: ConnectionManager, memory_graph: MemoryGraph | None = None):
        self.cm = cm
        self.memory = memory_graph or MemoryGraph(cm=cm)

    def index_research(
        self,
        artifact: Artifact,
        sources: list[ResearchSource],
        workspace_type: str | None = None,
        workspace_id: str | None = None,
    ) -> dict:
        """Index a completed research artifact into memory.
        
        Returns dict with counts of memories created per scope.
        """
        ...

    def get_relevant_memories(
        self,
        message: str,
        limit: int = 5,
    ) -> list[Memory]:
        """Retrieve research memories relevant to a message.
        
        Uses key_prefix matching against message keywords.
        Returns only memories with importance >= 4.
        """
        ...

    def compute_importance(self, source: ResearchSource) -> int:
        """Compute a 1-10 importance score from source metadata."""
        ...
```

### 4.2 Importance Scorer

```python
# toll/research/importance.py

class ImportanceScorer:
    """Computes and adjusts importance scores for research memories."""

    # Weights for initial score computation
    WEIGHTS = {
        "relevance": 0.4,
        "confidence": 0.3,
        "citations": 0.3,
    }

    def compute(self, source: ResearchSource) -> int:
        """Compute initial importance (1-10) from source metadata."""
        raw = (
            source.relevance_score * self.WEIGHTS["relevance"]
            + source.confidence_score * self.WEIGHTS["confidence"]
            + min(source.citation_count / 100, 1.0) * self.WEIGHTS["citations"]
        )
        return max(1, min(10, round(raw * 10)))

    def boost_on_retopic(self, topic: str, memory: Memory) -> int:
        """Increase importance when a topic is re-queried."""
        ...

    def decay_on_ignore(self, memory: Memory) -> int:
        """Decrease importance when a finding is unused."""
        ...
```

### 4.3 Context Engine Extension

The existing `ContextEngine._format_prompt()` already includes `[Relevant Memories]`. We extend it by adding a research-specific section when the flag is enabled:

```python
# In ContextEngine.build(), after memory retrieval:
if self.flags.is_enabled("research_memory_context"):
    research_memories = self.research_memory.get_relevant_memories(
        message, limit=5
    )
    memories.extend(research_memories)
```

No structural changes to `ContextResult` — research memories are merged into the existing `memories` list.

---

## 5. Storage Impact

### 5.1 New Table (Migration 0009)

The existing `memories` table is sufficient for storing research memories (type='knowledge'). But we need a secondary index for efficient topic-based lookup:

```sql
-- 0009_research_memory.sql

-- Research memory metadata: links memories back to research artifacts
-- and tracks per-source importance signals
CREATE TABLE IF NOT EXISTS research_memory_meta (
    memory_id TEXT PRIMARY KEY,
    artifact_id TEXT,
    source_id TEXT,
    topic TEXT NOT NULL,
    keywords TEXT NOT DEFAULT '[]',       -- JSON array of extracted keywords
    times_accessed INTEGER DEFAULT 0,
    times_retopic_hit INTEGER DEFAULT 0,
    last_boosted_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_research_memory_topic
    ON research_memory_meta(topic);
CREATE INDEX IF NOT EXISTS idx_research_memory_keywords
    ON research_memory_meta(keywords);
CREATE INDEX IF NOT EXISTS idx_research_memory_artifact
    ON research_memory_meta(artifact_id);
```

### 5.2 No New File Storage

All data is stored in SQLite. No new filesystem directories needed.

### 5.3 Migration 0009 Checklist

- Create `research_memory_meta` table with FK to `memories(id)`
- Add indexes on topic, keywords, artifact_id
- No existing data migration needed (new feature)

---

## 6. Feature Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `research_memory_auto_index` | `true` | Auto-index research results into MemoryGraph after `execute()` |
| `research_memory_context` | `false` | Inject research memories into ContextEngine prompts |
| `research_memory_importance_learn` | `true` | Enable importance adjustment via feedback loop |
| `research_memory_knowledge_vault` | `true` | Enable knowledge-vault cross-project lookup |
| `research_memory_max_context` | `5` | Max research memories to inject into context (stored in settings, not a flag) |

```python
RESEARCH_MEMORY_FLAGS: dict[str, bool] = {
    "research_memory_auto_index": True,
    "research_memory_context": False,   # opt-in; may increase token usage
    "research_memory_importance_learn": True,
    "research_memory_knowledge_vault": True,
}
```

These flags are registered in `feature_flags.py` during `_ensure_defaults()`.

---

## 7. ResearchService Integration Points

### 7.1 Post-Execute Hook

In `ResearchService.execute()`, after `self._store_sources(...)`:

```python
# End of execute(), before return:
if self.flags.is_enabled("research_memory_auto_index"):
    try:
        from ..research.memory_service import ResearchMemoryService
        rms = ResearchMemoryService(cm=self.cm)
        ws_type = metadata.get("workspace_type") if metadata else None
        ws_id = metadata.get("workspace_id") if metadata else None
        rms.index_research(
            artifact=artifact,
            sources=[ResearchSource(**s) for s in sources_data],
            workspace_type=ws_type,
            workspace_id=ws_id,
        )
    except Exception as e:
        logger.warning("Research memory indexing failed: %s", e)
```

Key: This is non-blocking — research execution succeeds regardless of memory indexing outcome. A warning is logged on failure.

### 7.2 Source Storage Enhancement

When storing sources in `SourceManager.store()`, also call into ResearchMemoryService to create per-source knowledge memories:

```python
# In SourceManager.store(), after successful INSERT:
if self.research_memory:
    self.research_memory.index_source(source, artifact_id)
```

This requires `ResearchMemoryService` to be available to `SourceManager`. We inject it via constructor or lazy-init with a flag check.

---

## 8. Implementation Plan

### Phase 1: Foundation (files 1–3)

| Step | File | What |
|------|------|------|
| 1.1 | `toll/research/importance.py` | `ImportanceScorer` class — compute/re-rank/decay logic |
| 1.2 | `toll/research/memory_service.py` | `ResearchMemoryService` — `index_research()`, `get_relevant_memories()`, `index_source()` |
| 1.3 | `toll/model/migrations/0009_research_memory.sql` | `research_memory_meta` table + indexes |

**Gate:** `ResearchMemoryService` unit tests pass; migration 0009 applies cleanly.

### Phase 2: Integration (files 4–7)

| Step | File | What |
|------|------|------|
| 2.1 | `toll/core/feature_flags.py` | Register `RESEARCH_MEMORY_FLAGS`; load during `_ensure_defaults` |
| 2.2 | `toll/application/research_service.py` | Add post-execute memory indexing hook (Section 7.1) |
| 2.3 | `toll/research/source_manager.py` | Add per-source memory indexing via optional `ResearchMemoryService` (Section 7.2) |
| 2.4 | `toll/context/engine.py` | Add research memory injection into `build()` (Section 4.3) |

**Gate:** Full integration test: research execute → memories created → context build includes them.

### Phase 3: Importance Learning (files 8–9)

| Step | File | What |
|------|------|------|
| 3.1 | `toll/research/memory_service.py` | Add `boost_on_retopic()`, `decay_on_ignore()`, `reindex_importance()` |
| 3.2 | `toll/application/research_service.py` | Track retopic queries → call `boost_on_retopic()` |

**Gate:** Retopic boost test: same topic queried twice → importance increases.

### Phase 4: Tests (10–12)

| Step | File | What |
|------|------|------|
| 4.1 | `tests/research/test_importance.py` | `ImportanceScorer` — compute, boost, decay, edge cases |
| 4.2 | `tests/research/test_memory_service.py` | `ResearchMemoryService` — index, retrieve, per-source, round-trip |
| 4.3 | `tests/api/test_research_memory_api.py` | Integration: execute → memories appear in context |

### Implementation Order Summary

```
Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4
  3 files     4 files     2 files     3 files
```

Total: **12 files** (6 new, 6 modified)

---

## 9. Detailed Class Specifications

### 9.1 ImportanceScorer

```python
@dataclass
class ImportanceSignal:
    memory_id: str
    source_id: str | None
    topic: str
    initial_score: int
    current_score: int
    times_accessed: int
    last_boosted_at: str | None
    created_at: str

class ImportanceScorer:
    def compute(self, source: ResearchSource) -> int
    def compute_from_findings(self, findings: list[str], source_count: int) -> int
    def boost_on_retopic(self, current_score: int, times_retopic: int) -> int
    def decay(self, current_score: int, days_since_access: int) -> int
    def should_include_in_context(self, memory: Memory, threshold: int = 4) -> bool
```

### 9.2 ResearchMemoryService

```python
class ResearchMemoryService:
    def __init__(self, cm: ConnectionManager, memory_graph: MemoryGraph | None = None)

    def index_research(
        self,
        artifact: Artifact,
        sources: list[ResearchSource],
        workspace_type: str | None = None,
        workspace_id: str | None = None,
    ) -> dict[str, int]:
        """Returns {'global': N, 'knowledge': N, 'project': N} counts."""

    def index_source(
        self,
        source: ResearchSource,
        artifact_id: str | None = None,
    ) -> Memory | None:
        """Index a single source as a knowledge-scope memory."""

    def get_relevant_memories(
        self,
        message: str,
        limit: int = 5,
        min_importance: int = 4,
    ) -> list[Memory]:
        """Keyword-match memories by topic/keywords."""

    def get_knowledge_vault(
        self,
        topic: str | None = None,
        limit: int = 50,
    ) -> list[Memory]:
        """Query all knowledge-scope memories, optionally filtered by topic."""

    def boost_on_retopic(
        self,
        topic: str,
        delta: int = 1,
    ) -> int:
        """Boost memories matching topic. Returns count boosted."""

    def decay_stale_memories(
        self,
        max_days: int = 90,
        delta: int = -1,
    ) -> int:
        """Decay memories not accessed in N days. Returns count decayed."""
```

### 9.3 Memory Key Conventions

Research memories follow a strict key convention for predictable lookup:

| Memory Type | entity_id | key pattern | value shape |
|-------------|-----------|-------------|-------------|
| `global` | `None` | `research:topic:{normalized_topic}` | `{"summary": str, "source_count": int, "artifact_id": str}` |
| `knowledge` | `source_id` | `research:source:{source_hash_prefix}` | `{"title": str, "authors": list, "year": int, "doi": str, "abstract": str, "artifact_id": str}` |
| `project` | `workspace_id` | `research:project:{workspace_id}:{topic}` | `{"summary": str, "date": str, "artifact_id": str}` |

This enables:
- `key LIKE 'research:topic:%'` — find all topic memories
- `key LIKE 'research:source:%'` — find all source memories
- `key LIKE 'research:project:{ws_id}:%'` — find project-scoped research

---

## 10. Knowledge Vault Semantics

The Knowledge Vault is not a separate component. It IS the set of all `type='knowledge'` memories in the MemoryGraph. What makes it a "vault":

1. **Cross-project persistence**: Knowledge memories have `entity_id=source_id` (not tied to any workspace). They survive workspace deletion and project switching.

2. **Dedup by DOI/URL**: Before creating a knowledge memory for a source, `ResearchMemoryService` checks if a memory with the same `key` (derived from DOI or URL) already exists. If so, it updates the existing memory instead of creating a duplicate.

3. **Keyword-based retrieval**: `get_knowledge_vault(topic)` queries `research_memory_meta` by topic or keyword JSON match to find relevant vault entries.

4. **Context filtering**: Only knowledge memories with `importance_score >= 4` are injected into context. This prevents low-value noise from cluttering prompts.

### Knowledge Vault API

Not a new API endpoint — accessed through the existing `memory_graph.query(type='knowledge', ...)` method plus the new `ResearchMemoryService.get_knowledge_vault()`. A future sprint may add REST endpoints for vault browsing.

---

## 11. Edge Cases

| Case | Handling |
|------|----------|
| Research with 0 sources | `index_research()` creates a single global memory with the synopsis; no source-level memories |
| Duplicate research topic | `key LIKE 'research:topic:{topic}'` — updates existing memory instead of creating duplicate |
| Source with no DOI/URL | Falls back to title-based key derivation (SHA256 prefix of normalized title) |
| Memory importance decay below 4 | Memory still exists in DB but excluded from context injection |
| Migration from pre-0009 | Fresh DDL; no data migration needed (new feature) |
| `research_memory_auto_index` disabled | No memory indexing; existing research flow unchanged |
| Research artifact deleted | `research_memory_meta` has FK → `memories(id)` CASCADE; orphaned meta rows cleaned by GC (future) |
| Very large research (100+ sources) | Indexing is O(N) but synchronous; caps at 50 sources per call in Phase 1 |
| Memory graph not yet initialized | `MemoryGraph(cm=cm)` handles missing tables gracefully via `_ensure_defaults`? Actually it doesn't — but the migration 0002 creates the memories table. If migration hasn't run, the code will fail with a DB error. This is acceptable — the try/except in the hook will catch it. |

---

## 12. Test Plan

### 12.1 Unit Tests — ImportanceScorer

| Test | What |
|------|------|
| `test_compute_from_high_relevance` | `relevance_score=1.0` → importance=10 |
| `test_compute_from_mid_values` | `relevance=0.6, confidence=0.5, citations=50` → importance=6 |
| `test_compute_from_low_values` | `relevance=0.1, confidence=0.1, citations=0` → importance=1 |
| `test_compute_from_source_no_metadata` | Empty source → importance=1 |
| `test_boost_on_retopic` | boost_on_retopic(5, 2) → returns 6 |
| `test_decay_by_days` | decay(5, 30) → returns 5 (no decay under 30d). decay(5, 100) → 4 |
| `test_should_include_in_context_threshold` | importance >= 4 → True. importance < 4 → False |

### 12.2 Unit Tests — ResearchMemoryService

| Test | What |
|------|------|
| `test_index_research_creates_memories` | execute() → global + knowledge + project memories created |
| `test_index_research_zero_sources` | No sources → only global memory (from synopsis) |
| `test_index_research_duplicate_topic` | Same topic twice → updates existing memory, no duplicate |
| `test_index_source_creates_knowledge` | Single source → knowledge memory with correct key/value |
| `test_index_source_dedup_by_doi` | Same DOI → no duplicate; updates existing |
| `test_get_relevant_memories_by_topic` | Query → returns matching topic memories |
| `test_get_relevant_memories_min_importance` | Only returns importance >= threshold |
| `test_get_knowledge_vault_all` | No filter → all knowledge memories |
| `test_get_knowledge_vault_by_topic` | Topic filter → subset |
| `test_boost_on_retopic` | Calls adjust_importance on matching memories |
| `test_decay_stale_memories` | Old memories get decayed |
| `test_round_trip_index_then_retrieve` | index → retrieve → verify all fields correct |

### 12.3 Integration Tests

| Test | File | What |
|------|------|------|
| `test_research_execute_indexes_memory` | `tests/api/test_research_memory_api.py` | Full research execute → memory appears in MemoryGraph |
| `test_context_includes_research_memory` | `tests/test_context_engine.py` | ContextEngine.build() includes research memories when flag enabled |
| `test_context_excludes_research_memory_flagged_off` | `tests/test_context_engine.py` | Flag disabled → no research memories in context |
| `test_research_memory_persists_across_sessions` | `tests/api/test_research_memory_api.py` | Memory survives service restart |

### 12.4 Edge Cases

| Case | Expected |
|------|----------|
| Index with no artifact_id | Still creates memories; `artifact_id` in meta is None |
| SourceManager.store() without ResearchMemoryService | No crash; source stored as before |
| ContextEngine.build() with no research memories | No research section; context assembled as before |
| Importance decay on never-accessed memory | `last_accessed_at` is `created_at`; decay applies normally |
| Concurrent research on same topic | Last writer wins; no crash due to UNIQUE index |

### 12.5 Test Count Target

| Category | Tests |
|----------|-------|
| ImportanceScorer unit | 7 |
| ResearchMemoryService unit | 11 |
| Integration | 4 |
| **Total** | **22** |

---

## 13. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Memory indexing slows down research execute | Low | Medium | Indexing is O(N) on sources; cap at 50 sources in try/except; warns on failure |
| Duplicate memories for same topic | Medium | Low | Key prefix convention + UNIQUE index on `memories(type, entity_id, key)` prevents duplicates |
| Context window bloated with research noise | Low | Medium | `min_importance=4` filter + `research_memory_context` flag opt-in; user controls max limit via settings |
| Migration 0009 fails on existing DB | Low | Medium | `CREATE TABLE IF NOT EXISTS` — idempotent; no data migration |
| Knowledge vault grows unbounded | Low | Low | `decay_stale_memories()` GC; importance decay pushes unused memories out of context |
| Per-source indexing creates too many memories | Medium | Low | 1 memory per source; typical research has 5-15 sources; even at 1000 sources it's ~1000 rows in SQLite |
| Research retopic detection is inaccurate | Medium | Low | Falls back to key_prefix matching; conservative (only exact topic matches). Can refine with AI-based topic extraction in future |

---

## 14. Summary of New Files

| File | Purpose |
|------|---------|
| `toll/research/importance.py` | `ImportanceScorer` — compute, boost, decay logic |
| `toll/research/memory_service.py` | `ResearchMemoryService` — index, retrieve, vault, retopic |
| `toll/model/migrations/0009_research_memory.sql` | `research_memory_meta` table + indexes |
| `tests/research/test_importance.py` | 7 unit tests for scorer |
| `tests/research/test_memory_service.py` | 11 unit tests for service |
| `tests/api/test_research_memory_api.py` | 4 integration tests |

## Modified Files

| File | Change |
|------|--------|
| `toll/core/feature_flags.py` | Register `RESEARCH_MEMORY_FLAGS` |
| `toll/application/research_service.py` | Post-execute memory indexing hook |
| `toll/research/source_manager.py` | Optional per-source memory indexing |
| `toll/context/engine.py` | Research memory injection into context |
| `toll/core/provider_selector.py` | (No change needed — memory isn't provider-selected) |
| `toll/memory/graph.py` | (No change needed — existing API is sufficient) |

## Deferred to Future Sprint

- Knowledge Vault REST API (CRUD endpoints for browsing vault memories)
- AI-based topic/keyword extraction from research synopsis
- Scheduled memory decay (cron-based GC)
- Research memory visualization in UI
- Cross-instance memory sync
- Memory importance explanation (why a memory scores N)
