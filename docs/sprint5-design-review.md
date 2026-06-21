# Sprint 5 Design Review — Research Layer

**Status:** Draft  
**Date:** 2026-06-21  
**Prerequisites:** Sprint 4 (Artifact System, Application Services, HandlerRegistry)

---

## 1. Architecture Overview

### Layered Research Pipeline

```
User Request
    │
    ▼
┌─────────────┐    ┌──────────────────┐
│   Planner   │───►│ Workflow Engine  │
└─────────────┘    └────────┬─────────┘
                            │
                    ┌───────┴────────┐
                    │ ResearchService │
                    └───────┬────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                  ▼
   ┌──────────┐     ┌──────────────┐   ┌────────────┐
   │  Source  │     │   Citation   │   │  Research  │
   │Management│     │   Engine     │   │  Memory    │
   └────┬─────┘     └──────┬───────┘   └─────┬──────┘
        │                  │                  │
        ▼                  ▼                  ▼
   ┌─────────────────────────────────────────────┐
   │           ResearchProvider (ABC)             │
   ├──────────┬──────────┬──────────┬────────────┤
   │NotebookLM│Semantic  │Google    │ ArXiv      │
   │          │Scholar   │Scholar   │            │
   ├──────────┼──────────┼──────────┼────────────┤
   │ Crossref │  Zotero  │Web Search│ Google     │
   │          │          │(DDG/...) │ Drive      │
   └──────────┴──────────┴──────────┴────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
   ┌─────────────────────────────────────────────┐
   │           Research Artifact                  │
   │  (sources + citations + synthesis + preview) │
   └─────────────────────────────────────────────┘
        │
        ▼
   ┌──────────┐   ┌──────────────┐
   │  Report  │   │ Presentation │
   │ Service  │   │   Service    │
   └──────────┘   └──────────────┘
```

### Package Layout

```
toll/
├── ports/
│   ├── research.py          ← ResearchProvider ABC (existing, expand)
│   └── research_source.py   ← New: source-specific provider port
│
├── research/                ← NEW: Research Layer
│   ├── __init__.py
│   ├── service.py           ← ResearchService orchestrator
│   ├── source_manager.py    ← Source collection, dedup, ranking
│   ├── citation_engine.py   ← Citation generation (APA, MLA, IEEE, Chicago)
│   ├── dedup.py             ← Source deduplication strategies
│   ├── retention.py         ← Research artifact retention policies
│   └── web_researcher.py    ← Web-based research provider (DDG + scrape)
│
├── adapters/
│   └── research/            ← NEW: provider adapters
│       ├── __init__.py
│       ├── notebooklm.py        ← NotebookLM adapter
│       ├── semantic_scholar.py  ← Semantic Scholar API adapter
│       ├── google_scholar.py    ← Google Scholar scraper adapter
│       ├── arxiv.py             ← ArXiv API adapter
│       ├── crossref.py          ← Crossref API adapter
│       ├── zotero.py            ← Zotero API adapter
│       └── google_drive.py      ← Google Drive adapter
│
├── application/
│   ├── research_service.py  ← NEW: Workflow handler (matches carousel_service pattern)
│   └── handler_registry.py  ← MODIFY: register research handlers
│
├── workspace/
│   └── manager.py           ← MODIFY: add research_config to workspace metadata
│
└── model/
    ├── artifact.py          ← MODIFY: add ArtifactType.RESEARCH
    └── migrations/
        └── 0005_research.sql ← NEW: sources, citations, dedup tables

api/routers/
├── research.py              ← NEW: research API endpoints
└── artifacts.py             ← MODIFY: research-specific content/preview routes
```

---

## 2. Research Service Architecture

### Responsibilities

`ResearchService` is the central orchestrator. It mirrors `CarouselService`/`ReportService` but is research-specific:

- Receives a research query from the WorkflowEngine
- Determines which provider(s) to query (via ProviderSelector extended with research types)
- Collects sources from selected provider(s)
- Runs deduplication on collected sources
- Generates citations in the requested style
- Stores sources, citations, and synthesis as a Research Artifact
- Writes preview HTML/JSON
- Reports result back to WorkflowEngine

### Data Flow

```
1. HandlerRegistry routes "research" intent → ResearchService.execute()
2. ResearchService:
   a. Extracts query parameters from plan (topic, depth, max_sources, citation_style, include_drive)
   b. Selects provider(s) via ProviderSelector.select(ArtifactType.RESEARCH)
   c. Calls SourceManager.collect(query) → gathers from all enabled providers
   d. Calls SourceManager.deduplicate(sources) → merged list
   e. Calls CitationEngine.format(sources, style) → citation strings
   f. Calls AI for synthesis (topic + deduplicated sources + citations)
   g. Creates Research Artifact with sources + citations + synthesis
   h. Writes preview HTML via dedicated ResearchPreviewRenderer
   i. Returns artifact_id + preview_url
```

### API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/research/search` | Execute a research query |
| `GET` | `/api/research/sources` | List all sources (filterable) |
| `GET` | `/api/research/sources/{id}` | Get source details |
| `GET` | `/api/research/sources/{id}/cite` | Get citation for a source |
| `DELETE` | `/api/research/sources/{id}` | Delete a source |
| `POST` | `/api/research/sources/{id}/tag` | Add tags to a source |
| `POST` | `/api/research/sources/import` | Import sources (Zotero, RIS, BibTeX) |
| `GET` | `/api/research/artifacts` | List research artifacts (lives under `/api/artifacts?type=research`) |
| `GET` | `/api/research/artifacts/{id}/sources` | Get sources for a research artifact |
| `GET` | `/api/research/artifacts/{id}/citations` | Get citations for a research artifact |
| `GET` | `/api/research/artifacts/{id}/export` | Export as RIS/BibTeX |
| `GET` | `/api/research/artifacts/{id}/export/{format}` | Export in specific citation format |

### Feature Flags

| Flag | Default | Description |
|---|---|---|
| `research_provider` | `false` | Master toggle for research layer |
| `provider_notebooklm` | `false` | NotebookLM integration |
| `provider_semantic_scholar` | `false` | Semantic Scholar API |
| `provider_google_scholar` | `false` | Google Scholar scraping |
| `provider_arxiv` | `false` | ArXiv API |
| `provider_crossref` | `false` | Crossref API |
| `provider_zotero` | `false` | Zotero API |
| `google_drive_integration` | `false` | Google Drive source import |
| `citation_engine` | `false` | Citation generation |
| `source_dedup` | `false` | Source deduplication |
| `research_memory` | `false` | Research memory integration |
| `research_retention` | `false` | Research retention policy |

### Storage Model (Migration 0005)

```sql
CREATE TABLE IF NOT EXISTS research_sources (
    id TEXT PRIMARY KEY,
    artifact_id TEXT,                    -- NULL = standalone, non-artifact source
    title TEXT NOT NULL,
    authors TEXT DEFAULT '[]',           -- JSON array
    year INTEGER,
    journal TEXT,
    doi TEXT,
    url TEXT,
    abstract TEXT,
    full_text_hash TEXT,                 -- SHA256 for dedup
    source_type TEXT NOT NULL,           -- 'journal', 'book', 'conference', 'web', 'thesis', 'report'
    provider TEXT NOT NULL,              -- which provider returned this
    provider_source_id TEXT,             -- provider's own ID (DOI, arXiv ID, etc.)
    citation_count INTEGER DEFAULT 0,
    relevance_score REAL DEFAULT 0.0,
    tags TEXT DEFAULT '[]',
    metadata TEXT DEFAULT '{}',
    access_type TEXT DEFAULT 'open',     -- 'open', 'restricted', 'closed'
    language TEXT DEFAULT 'ar',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (artifact_id) REFERENCES artifacts(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS research_citations (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    artifact_id TEXT,
    style TEXT NOT NULL DEFAULT 'apa',    -- 'apa', 'mla', 'ieee', 'chicago'
    citation TEXT NOT NULL,              -- formatted citation string
    created_at TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES research_sources(id) ON DELETE CASCADE,
    FOREIGN KEY (artifact_id) REFERENCES artifacts(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS research_dedup_log (
    id TEXT PRIMARY KEY,
    source_a_id TEXT NOT NULL,
    source_b_id TEXT NOT NULL,
    strategy TEXT NOT NULL,               -- 'doi', 'title_similarity', 'url', 'hash'
    similarity_score REAL NOT NULL,
    merged_into TEXT NOT NULL,            -- which ID survived
    created_at TEXT NOT NULL,
    FOREIGN KEY (source_a_id) REFERENCES research_sources(id),
    FOREIGN KEY (source_b_id) REFERENCES research_sources(id)
);

CREATE TABLE IF NOT EXISTS research_memory (
    id TEXT PRIMARY KEY,
    artifact_id TEXT,
    source_ids TEXT DEFAULT '[]',         -- JSON array of source IDs
    topic TEXT NOT NULL,
    synthesis TEXT,                       -- AI-generated synthesis
    key_findings TEXT DEFAULT '[]',       -- JSON array
    citation_ids TEXT DEFAULT '[]',       -- JSON array
    workspace_type TEXT,
    workspace_id TEXT,
    semester_id TEXT,
    created_at TEXT NOT NULL,
    expires_at TEXT,                      -- retention policy
    importance_score INTEGER DEFAULT 5,
    FOREIGN KEY (artifact_id) REFERENCES artifacts(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_sources_artifact ON research_sources(artifact_id);
CREATE INDEX IF NOT EXISTS idx_sources_provider ON research_sources(provider);
CREATE INDEX IF NOT EXISTS idx_sources_hash ON research_sources(full_text_hash);
CREATE INDEX IF NOT EXISTS idx_sources_doi ON research_sources(doi);
CREATE INDEX IF NOT EXISTS idx_citations_source ON research_citations(source_id);
CREATE INDEX IF NOT EXISTS idx_citations_style ON research_citations(style);
CREATE INDEX IF NOT EXISTS idx_research_memory_topic ON research_memory(topic);
CREATE INDEX IF NOT EXISTS idx_research_memory_semester ON research_memory(semester_id);
CREATE INDEX IF NOT EXISTS idx_research_memory_expires ON research_memory(expires_at);
```

### Future Expansion Path

- Multi-provider parallel queries: fan-out to all enabled providers simultaneously, merge results
- Async streaming: return partial results as each provider responds
- Citation graph: visualize how sources cite each other
- Research collections: group artifacts into research projects
- Full-text caching: store full-text of open-access sources locally
- Semantic search over cached full-text via vector embeddings
- Multi-user: add `user_id` column to all research tables, scope queries by active user

---

## 3. ResearchProvider Architecture

### Current State

`toll/ports/research.py` defines a `ResearchProvider` ABC with three methods:

```python
class ResearchProvider(ABC):
    def search(self, query: ResearchQuery) -> ResearchResult: ...
    def cite(self, source: ResearchSource, style: str = "apa") -> str: ...
    def synthesize(self, sources: list[ResearchSource], topic: str) -> str: ...
```

### Expanded Design

The ABC is expanded to support richer provider capabilities:

```python
class ResearchProvider(ABC):
    name: str                         # provider identifier
    supported_styles: list[str]       # which citation styles this provider supports
    max_sources_per_query: int

    def search(self, query: ResearchQuery) -> ResearchResult
    def search_by_ids(self, ids: list[str]) -> list[ResearchSource]   # fetch by DOI/ID
    def cite(self, source: ResearchSource, style: str = "apa") -> str
    def synthesize(self, sources: list[ResearchSource], topic: str) -> str
    def is_available(self) -> bool
    def rate_limit_remaining(self) -> int | None
```

### ResearchQuery Expansion

```python
@dataclass
class ResearchQuery:
    query: str
    max_sources: int = 10
    style: str = "apa"                # citation style
    include_full_text: bool = False
    providers: list[str] | None = None  # restrict to specific providers
    year_from: int | None = None
    year_to: int | None = None
    source_types: list[str] | None = None  # journal, book, conference, etc.
    language: str | None = None
```

### Provider Capability Matrix

| Provider | Search | By ID | Cite | Synthesize | Rate-limited | API key |
|---|---|---|---|---|---|---|
| WebSearch (DDG) | ✓ | — | — | — | No | No |
| NotebookLM | ✓ | — | ✓ | ✓ | Yes | Yes |
| Semantic Scholar | ✓ | ✓ | ✓ | — | Yes | Optional |
| Google Scholar | ✓ | — | ✓ | — | Yes | No |
| ArXiv | ✓ | ✓ | ✓ | — | No | No |
| Crossref | ✓ | ✓ | ✓ | — | Yes | No |
| Zotero | ✓ | ✓ | ✓ | — | No | Yes |

### Provider Request Flow

```
SourceManager.collect(query)
    │
    ├──► ResearchProvider.search(query)          — general search
    ├──► ResearchProvider.search_by_ids(ids)     — fetch specific known sources
    └──► (parallel) for each configured provider
              │
              ▼
         Normalized ResearchSource list
              │
              ▼
         SourceManager.deduplicate(sources)
```

### Web-Based Research Provider (Fallback)

A `WebResearcher` adapter (not a full `ResearchProvider`) serves as the fallback when no dedicated research API is configured. It:

1. Uses the existing DuckDuckGo search adapter to find web results
2. Scrapes the first N results for title, snippet, and URL
3. Coerces results into `ResearchSource` format with `source_type="web"`
4. Generates simple web citations via citation engine
5. Is always available (no API key needed)

This ensures the research pipeline works out of the box even without any research API keys.

---

## 4. NotebookLM Integration Strategy

### Capabilities

NotebookLM (powered by Gemini) provides:
- Source-grounded Q&A over uploaded documents (PDFs, web URLs, YouTube transcripts, Google Docs, Slides)
- Auto-generated podcast-style Audio Overviews (two AI hosts discuss uploaded sources)
- Source-specific citations grounded in uploaded material
- Notebook organization (sources grouped into "notebooks")
- Source summaries and key topics extraction

### Integration Approach

The adapter wraps the NotebookLM consumer API (or Google AI Gemini API with grounding):

```python
class NotebookLMAdapter(ResearchProvider):
    name = "notebooklm"
```

**Phase 1 — Reading (V1):**
- Upload URLs or text snippets as sources
- Query grounded answers with source citations
- Store citations in research_citations table

**Phase 2 — Writing (V2):**
- Create notebooks programmatically
- Upload local PDFs from `data/research/` to NotebookLM
- Export Audio Overview as podcast artifact

**Phase 3 — Sync (V3):**
- Two-way sync: sources added in NotebookLM appear in toll's source list
- Poll notebook changes via API

### Data Flow

```
ResearchService
    │
    ▼
NotebookLMAdapter.search(query)
    │
    ├──► Upload source materials (URLs/text) to notebook
    ├──► Ask grounded question (query)
    ├──► Extract cited sources and citations
    └──► Return ResearchResult with grounded citations
```

### Limitations

- API is rate-limited (consumer version: ~50 queries/day)
- No bulk search over NotebookLM's own knowledge base
- Only cites from sources you upload — does not independently discover new sources
- Audio Overview generation is slow (~5 min) and may need async polling

### Feature Flag: `provider_notebooklm`

---

## 5. Google Drive Integration Strategy

### Capabilities

Google Drive research integration provides:
- Uploading research artifacts (reports, presentations) to Drive folders
- Importing Drive documents as research sources (PDF papers, Google Docs notes)
- Organizing artifacts per semester or research project in Drive
- Auto-attaching Drive links to research artifacts for easy sharing

### Integration Approach

A dedicated `GoogleDriveAdapter` that is NOT a `ResearchProvider` (Drive does not do research search) but exposes:

```python
class GoogleDriveAdapter:
    name = "google_drive"

    def upload_artifact(self, artifact: Artifact, folder_id: str | None = None) -> str
    def import_sources(self, folder_id: str, mime_types: list[str] | None = None) -> list[ResearchSource]
    def create_folder(self, name: str, parent_id: str | None = None) -> str
    def find_or_create_semester_folder(self, semester: dict, university: dict) -> str
```

**Phase 1 — Export (V1):**
- Research artifacts auto-upload to Drive on completion
- Folder structure mirrors the semester/university workspace hierarchy
- Uploaded file reference stored in artifact metadata

**Phase 2 — Import (V2):**
- User selects a Drive folder to scan for research PDFs
- Files imported as `ResearchSource` with `provider="google_drive"`
- Full-text extracted for local search

**Phase 3 — Sync (V3):**
- Watch Drive folder for new files via push notifications
- Auto-import new papers into source library

### Folder Structure Convention

```
Drive/
└── Toll Research/
    ├── [University Name]/
    │   ├── Semester 1/
    │   │   ├── Reports/
    │   │   ├── Presentations/
    │   │   └── Sources/
    │   ├── Semester 2/
    │   └── ...
    └── General/
```

### Feature Flag: `google_drive_integration`

---

## 6. Citation Engine

### Responsibilities

The Citation Engine generates formatted citations in multiple academic styles. It operates on `ResearchSource` objects and produces strings stored in `research_citations`.

### Supported Styles

| Style | Format | Use Case |
|---|---|---|
| APA 7th | `Author, A. A. (Year). Title. Journal, Volume(Issue), Pages. DOI` | Psychology, Education, Sciences |
| MLA 9th | `Author, A. A. "Title." Journal, vol. Volume, no. Issue, Year, pp. Pages.` | Humanities, Literature |
| IEEE | `[1] A. A. Author, "Title," Journal, vol. X, no. Y, pp. Z, Year.` | Engineering, Computer Science |
| Chicago (Notes) | `Author, A. A. "Title." Journal Volume, no. Issue (Year): Pages. DOI` | History, Arts |
| Chicago (Author-Date) | `Author, A. A. Year. "Title." Journal Volume (Issue): Pages. DOI` | Social Sciences |
| Vancouver | `1. Author AA. Title. Journal. Year;Volume(Issue):Pages.` | Medicine, Biomedicine |

### Data Flow

```
CitationEngine.format(source: ResearchSource, style: str = "apa") → str
    │
    ├──► Normalize author names
    ├──► Extract year from source
    ├──► Format based on style template
    ├──► Append DOI/URL if available
    └──► Return formatted string
```

### Batch Operations

```python
class CitationEngine:
    def format(self, source: ResearchSource, style: str = "apa") -> str: ...
    def format_batch(self, sources: list[ResearchSource], style: str = "apa") -> list[str]: ...
    def export_bibtex(self, sources: list[ResearchSource]) -> str: ...
    def export_ris(self, sources: list[ResearchSource]) -> str: ...
```

### Future Expansion Path

- User-defined custom style templates stored in config
- Citation library export (BibTeX, RIS, CSV) for import into Zotero/Mendeley
- In-text citation insertion: `(Author, Year)` → highlighted in report body
- Citation network visualization (source → source references)

**Important Design Decision:** The Citation Engine generates citations from structured data, NOT by calling an external API for every citation. External APIs (Crossref, Zotero) provide the structured data; the engine formats it locally.

---

## 7. Source Management

### Responsibilities

`SourceManager` handles the lifecycle of research sources:

- Collection: Gather sources from all enabled providers
- Deduplication: Merge duplicate sources from different providers
- Ranking: Sort by relevance_score (provider-specific + configurable weights)
- Tagging: User and auto-tags (via AI categorization)
- Import: Bulk import from BibTeX, RIS, Zotero JSON
- Export: Export selected sources to citation formats

### Source Types

```python
class SourceType(str, Enum):
    JOURNAL = "journal"
    BOOK = "book"
    BOOK_CHAPTER = "book_chapter"
    CONFERENCE = "conference"
    THESIS = "thesis"
    REPORT = "report"
    WEB = "web"
    PREPRINT = "preprint"
    DATASET = "dataset"
    SOFTWARE = "software"
    OTHER = "other"
```

### Collection Flow

```
SourceManager.collect(query: ResearchQuery) → list[ResearchSource]
    │
    ├──► For each enabled provider:
    │       ├──► Check rate limits
    │       ├──► Call provider.search(query)
    │       ├──► Normalize results to ResearchSource
    │       └──► Store raw results in research_sources (artifact_id = NULL)
    │
    ├──► SourceManager.deduplicate(all_raw_sources) → merged list
    ├──► SourceManager.rank(merged) → sorted by relevance
    │
    └──► Return ranked list
```

### Source Lifecycle

```
Raw (from provider) → Normalized (dedup + rank) → Attached (to artifact) → Cited (citation generated) → Archived (retention)
```

---

## 8. Research Artifact Type

### New ArtifactType

```python
class ArtifactType(str, Enum):
    # ... existing types ...
    RESEARCH = "research"         # NEW
```

### Research Content Schema

```python
artifact.content = {
    "type": "research",
    "query": ResearchQuery,
    "sources": [ResearchSource, ...],           # deduplicated sources
    "source_count": int,
    "citation_count": int,
    "synopsis": str,                             # AI-generated synthesis
    "key_findings": [str, ...],                  # AI-extracted findings
    "citations": [str, ...],                     # formatted citations
    "style": str,                                # citation style used
    "provider_results": {                        # per-provider metadata
        "semantic_scholar": {"sources_found": 5, "latency_ms": 340},
        "arxiv": {"sources_found": 3, "latency_ms": 120},
    },
}
```

### Artifact Metadata

```python
artifact.metadata = {
    "research_depth": "quick" | "standard" | "deep",
    "citation_style": "apa",
    "provider_count": int,
    "dedup_removed": int,                        # sources removed by dedup
    "semester_id": str | None,
    "university_id": str | None,
}
```

### Preview

A `ResearchPreviewRenderer` generates:
- `preview.html`: Source list with citations, synopsis card, key findings
- `preview.json`: Full structured data for programmatic consumption

### API Response Enrichment

Existing artifact endpoints already return type-specific content. The `/api/artifacts/{id}/content` endpoint will return the research content structure directly. New endpoints (listed in Section 2) add research-specific views: `/sources`, `/citations`, `/export/{format}`.

---

## 9. Academic Workspace Integration

### How It Fits

The workspace manager already supports `university` workspaces with semesters. Research artifacts plug into this:

```python
# Workspace metadata expanded (stored in metadata JSON):
{
    "university": "King Saud University",
    "college": "College of Computer Science",
    "major": "Computer Science",
    "semesters": [...],
    "research_config": {                        # NEW
        "default_citation_style": "apa",
        "preferred_providers": ["semantic_scholar", "arxiv"],
        "auto_upload_to_drive": False,
        "retention_days": 365,
        "max_sources_per_query": 20,
    },
}
```

### Semester Integration

**Scenario: Student in Semester 2 at KSU researching NLP techniques**

```
1. User activates workspace: /university "KSU" → sets active_*
2. User creates semester: /semester "Semester 2" → active_semester_id set
3. User searches: "ابحث عن تقنيات معالجة اللغة العربية"
4. Planner detects "research" intent
5. WorkflowEngine routes to ResearchService
6. ResearchService:
   a. Reads active workspace context (KSU, Semester 2)
   b. Reads semester metadata for default citation style, preferred providers
   c. Runs research query
   d. Tags artifact with workspace_type="university", workspace_id=KSU id
   e. Sets semester_id in artifact metadata
   f. Creates research artifact
   g. Result flows to ReportService or PresentationService for output
7. Artifact is retrievable filtered by semester_id
```

### Context Engine Integration

The context engine (`toll/context/engine.py`) builds LLM prompts from:
- Active workspace state
- Relevant memories
- Recent conversation history

**Expansion for research:** Include recent research artifacts relevant to the current topic in the context window, so the AI can reference past research findings in new conversations.

---

## 10. Semester-Aware Research Workflows

### Workflow Definitions

The planner gets new intents for research:

```python
class Planner:
    MATRIX = {
        # ... existing ...
        "research_quick": ApprovalLevel.AUTO,         # Quick search, no output artifact
        "research": ApprovalLevel.APPROVAL,            # Full research → artifact
        "research_deep": ApprovalLevel.APPROVAL,       # Deep research (all providers)
    }

    KEYWORDS = {
        # ... existing ...
        "research": ["research", "ابحث", "بحث", "study about", "sources about",
                     "اقتراح مصادر", "academic search", "doi"],
        "research_quick": ["quick research", "ابحث سريعا", "tell me about"],
        "research_deep": ["deep research", "بحث عميق", "comprehensive search"],
    }
```

### Semester-Aware Data Flow

```
User: "ابحث عن تقنيات معالجة اللغة العربية في الفصل الدراسي الثاني"
    │
    ▼
Planner → intent="research", level=APPROVAL
    │
    ▼
WorkflowEngine.create(plan, metadata={conversation_id})
    │  (plan contains semester_id from active workspace context)
    ▼
ResearchService.execute(plan, metadata)
    │
    ├──► ContextEngine.build() includes active semester in prompt
    ├──► All sources stored with semester_id
    ├──► Research artifact tagged with workspace_type="university", workspace_id, semester_id
    │
    ▼
HandlerRegistry responds to user with artifact_id + preview_url
```

### Cross-Semester Research

When no semester is active, research is tagged as `workspace_type="university"` with `semester_id=None`. Users can:
- List research artifacts across all semesters
- Filter by semester
- Compare sources used in different semesters

---

## 11. Research Memory Integration

### Memory Types

The memory graph (`toll/memory/graph.py`) stores typed memories. Research adds:

| Memory Type | entity_id | key | value |
|---|---|---|---|
| `research` | `user_id` | `recent_topics` | `["NLP", "Machine Learning", ...]` |
| `research` | `semester_id` | `explored_topics` | `["Topic A", "Topic B"]` |
| `research` | `artifact_id` | `key_findings` | `["Finding 1", "Finding 2"]` |
| `research` | `source_id` | `source_summary` | `"Summary of the paper"` |

### Automatic Memory Creation

On research completion, ResearchService calls `MemoryGraph.store()` for:

1. **Topic memory:** Store the research topic with importance 5
2. **Key findings:** Store each key finding as a separate memory
3. **Provider usage:** Store which providers were most useful (importance adjusted via `learn_from_feedback`)

### Context Injection

When the context engine builds a prompt for a user in an academic workspace, it queries:

```python
memories = self.memory.retrieve(
    type="research",
    entity_id=active_semester_id,   # get research memories for this semester
    limit=5,
)
```

This injects recent research findings into the LLM context automatically.

---

## 12. Source Deduplication Strategy

### Strategies (Applied in Order)

| Strategy | Method | Strength |
|---|---|---|
| **DOI Match** | Exact DOI comparison | 100% — no false positives |
| **URL Match** | Normalized URL comparison | High — same web source from different providers |
| **Title Similarity** | Fuzzy string matching (Levenshtein / token overlap) | Medium — catches formatting differences |
| **Content Hash** | SHA256 of first 1KB of abstract/full-text | High — same paper from different sources |
| **Author+Year+Title** | Composite key: normalized author + year + title lowercase | Medium — different versions of same work |

### Algorithm

```
SourceManager.deduplicate(sources: list[ResearchSource]) → list[ResearchSource]
    │
    ├──► Group by DOI (fast path, O(n) hash lookup)
    │       └──► Keep highest relevance_score, log in dedup_log
    │
    ├──► Group by normalized URL
    │       └──► Keep highest relevance_score, log remainder
    │
    ├──► Group by content hash (only if include_full_text=True)
    │       └──► Keep first, log remainder
    │
    ├──► Group by title similarity (pairwise, O(n²) but n ≤ max_sources ≤ 100)
    │       └──► Levenshtein ratio > 0.85 → merge
    │       └──► Token overlap (Jaccard) > 0.7 → merge
    │
    ├──► Group by author+year+title composite
    │       └──► Normalize: lowercase, strip punctuation, tokenize
    │       └──► Exact match on composite key → merge
    │
    └──► Return ranked by relevance_score
```

### Storage

All dedup decisions are logged to `research_dedup_log` for auditability. The `merged_into` field tracks which source ID survived, enabling:

- Undo: If a merge is wrong, promote the removed source back
- Analysis: Report on how much duplication exists across providers
- Tuning: Adjust similarity thresholds based on false positive rate

---

## 13. Research Retention Policy

### Policy Table

| Type of Data | Retention | Exemption |
|---|---|---|
| Sources (standalone, no artifact) | 30 days | Tagged sources: 365 days |
| Sources (attached to artifact) | Lifetime of artifact | Archiving artifact moves sources to cold storage |
| Citations | Lifetime of artifact | Same as attached sources |
| Dedup logs | 90 days | — |
| Research memories | 365 days | Adjusted by importance: score ≥ 8 → permanent |
| Research artifacts (standard) | 365 days | Extended by semester metadata |
| Research artifacts (semester) | End of semester + 180 days | Active semester: no expiry |
| Google Drive uploads | Not managed (external) | — |

### Implementation

The `retention.py` module provides:

```python
class ResearchRetention:
    def apply(self, days_past: int = 30):
        """Run retention policy. Called by a scheduled task or on startup."""
        # 1. Expire standalone sources older than 30 days (unless tagged)
        # 2. Expire dedup logs older than 90 days
        # 3. Archive research artifacts past their semester + 180 days
        # 4. Downgrade importance of stale research memories
```

### Semester-Aware Expiry

When a semester is closed (user calls `/semester close`):

```python
if semester.end_date < now:
    # All research artifacts for this semester get expires_at = now + 180 days
    # Research memories downgraded to importance score -2
    # Sources not attached to an active-semester artifact expire in 30 days
```

---

## 14. Future Providers

### NotebookLM

| Attribute | Detail |
|---|---|
| Port | `ResearchProvider` |
| API | Google Gemini API with grounding / NotebookLM consumer API |
| Cost | Free tier: ~50 queries/day; paid: Gemini API pricing |
| Setup | User provides Gemini API key |
| Strength | Grounded Q&A over user-uploaded sources |
| Weakness | Cannot discover new sources independently |
| Phase 1 | Basic grounded query → citations |
| Phase 2 | Notebook creation, PDF upload |
| Phase 3 | Audio Overview export |

### Semantic Scholar

| Attribute | Detail |
|---|---|
| Port | `ResearchProvider` |
| API | Semantic Scholar Academic Graph API (REST, free, no key for basic) |
| Cost | Free: 100 requests/sec; Tiered: API key for higher limits |
| Setup | Optional API key for higher rate limits |
| Strength | Strong paper search, citation graph, TLDR summaries |
| Endpoints | `/paper/search`, `/paper/{id}`, `/recommendations` |
| Phase 1 | Paper search → sources + citations |
| Phase 2 | Citation graph traversal (who cites whom) |
| Phase 3 | Recommendations based on source list |

### Google Scholar

| Attribute | Detail |
|---|---|
| Port | `ResearchProvider` |
| API | Scraping (no official public API) |
| Cost | Free (rate-limited scraping) |
| Setup | None |
| Strength | Broadest coverage of academic sources |
| Weakness | Unreliable scraping, CAPTCHA risk, no structured data |
| Phase 1 | Basic scraping with polite delays |
| Phase 2 | Cached results to minimize scraping |
| Phase 3 | Proxy rotation for reliability |

### ArXiv

| Attribute | Detail |
|---|---|
| Port | `ResearchProvider` |
| API | ArXiv API (REST, free, no key) |
| Cost | Free |
| Setup | None |
| Strength | Full-text of preprints, good for CS/Physics/Math |
| Endpoints | `/api/query`, OAI-PMH for metadata |
| Phase 1 | Paper search → sources |
| Phase 2 | Full-text download → local search |
| Phase 3 | New paper alerts by topic |

### Crossref

| Attribute | Detail |
|---|---|
| Port | `ResearchProvider` |
| API | Crossref REST API (free, polite pool) |
| Cost | Free |
| Setup | Optional email for better rate limits |
| Strength | DOI resolution, metadata completeness, citation counts |
| Endpoints | `/works`, `/works/{doi}`, `/funders` |
| Phase 1 | DOI lookup → citation formatting |
| Phase 2 | Search by title/author |
| Phase 3 | Funding information enrichment |

### Zotero

| Attribute | Detail |
|---|---|
| Port | `ResearchProvider` (Read) |
| API | Zotero API (REST, needs API key) |
| Cost | Free (300 MB storage, unlimited WebDAV) |
| Setup | Zotero account + API key |
| Strength | User's personal library, organized collections, full item metadata |
| Endpoints | `/users/{id}/items`, `/users/{id}/collections/{id}/items` |
| Phase 1 | Import user's Zotero library as sources |
| Phase 2 | Sync: new Zotero items auto-imported |
| Phase 3 | Export toll citations back to Zotero |

---

## 15. University Task Flow (End-to-End)

### Complete Flow: User requests a research-backed report

```
User: "اكتب تقريراً عن تقنيات معالجة اللغة العربية في الفصل الدراسي الثاني"

    │
    ▼
┌───────────────────────────────────────────────────────────┐
│ 1. Planner                                                 │
│    - Classifies: intent="research", level=APPROVAL         │
│    - Sets mode from flags (STRICT/BALANCED/FAST)          │
│    - Returns Plan with intent, title, description          │
└───────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────┐
│ 2. WorkflowEngine                                          │
│    - Creates workflow: status=PENDING (needs approval)     │
│    - Returns workflow_id to user                           │
│    - User approves: workflow.status → APPROVED             │
│    - Engine.run(workflow_id): status → RUNNING             │
│    - Looks up handler for intent="research"                │
└───────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────┐
│ 3. ResearchService.execute(plan, metadata)                 │
│    - Reads conversation_id, workspace context from metadata │
│    - Extracts: topic, max_sources, style                   │
│    - Detects active semester from workspace state           │
│    - Builds ResearchQuery(query, style, ...)               │
└───────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────┐
│ 4. ProviderSelector.select(ArtifactType.RESEARCH)          │
│    - Checks flag: research_provider                        │
│    - Checks enabled providers: semantic_scholar?, arxiv?   │
│    - Checks user preference (settings)                     │
│    - Returns best provider name(s)                         │
└───────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────┐
│ 5. Source Collection (per provider)                        │
│    - Semantic Scholar: search(query, max_sources=10)       │
│    - ArXiv: search(query, max_sources=5)                   │
│    - WebResearcher (fallback): DDG search + scrape         │
│    - Each returns list[ResearchSource]                     │
└───────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────┐
│ 6. Source Deduplication                                    │
│    - Merge by DOI, URL, title similarity, content hash     │
│    - Keep highest relevance_score per group                │
│    - Log merges in research_dedup_log                      │
│    - Return ranked, deduplicated list                      │
└───────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────┐
│ 7. Citation Engine                                         │
│    - For each source: CitationEngine.format(source, "apa") │
│    - Store in research_citations table                     │
│    - Return formatted citation strings                     │
└───────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────┐
│ 8. Research Artifact Creation                              │
│    - Create: Artifact(type=RESEARCH, status=DRAFT,         │
│               content={sources, citations, query})         │
│    - Store sources in research_sources (linked to artifact)│
│    - Store citations in research_citations                 │
│    - Set workspace_type="university", workspace_id=ksu_id  │
│    - Set semester_id in artifact metadata                  │
│    - Write preview.html, preview.json                      │
│    - Artifact status → COMPLETED                           │
└───────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────┐
│ 9. Research Memory Integration                             │
│    - MemoryGraph.store("research", "recent_topics", topic) │
│    - MemoryGraph.store("research", semester_id,            │
│                        "explored_topics", [topic, ...])    │
│    - For each key finding: MemoryGraph.store(...)          │
│    - Adjust provider importance based on result quality    │
└───────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────┐
│ 10. Report Generation (optional downstream)                │
│     - ResearchService returns artifact_id                  │
│     - If user requested report:                            │
│       └──► ReportService.execute with                     │
│             research_artifact_id in plan                   │
│             └──► ReportRenderer includes citations        │
│                   from research artifact                   │
│     - If user requested presentation:                      │
│       └──► PresentationService.execute with               │
│             research_artifact_id in plan                   │
└───────────────────────────────────────────────────────────┘
    │
    ▼
User receives: research artifact link + citations + synopsis
(and optionally: linked report/presentation with embedded citations)
```

### Approval Flow Matrix

| Intent | Level | Description |
|---|---|---|
| `research_quick` | AUTO | Quick web search, no artifact created |
| `research` | APPROVAL | Full research pipeline, creates artifact |
| `research_deep` | APPROVAL | All providers, deeper collection |

### Artifact Chain

```
Research Artifact (sources + citations)
    │
    ├──► Report Artifact (content with citations)
    │       └──► Rendered HTML report with footnote citations
    │
    └──► Presentation Artifact (slides with references)
            └──► Rendered HTML deck with reference slide
```

---

## 16. Planner Integration

### New Intents

```python
class Planner:
    MATRIX = {
        # ... Sprint 4 matrix ...
        "research_quick": ApprovalLevel.AUTO,
        "research": ApprovalLevel.APPROVAL,
        "research_deep": ApprovalLevel.APPROVAL,
        # Future:
        "source_import": ApprovalLevel.APPROVAL,     # Import BibTeX/Zotero
        "citation_export": ApprovalLevel.AUTO,        # Export citations
    }

    KEYWORDS = {
        # ... Sprint 4 keywords ...
        "research_quick": ["tell me about", "quick research", "what is known about",
                          "معلومات عن", "اخبرني عن"],
        "research": ["research", "ابحث", "بحث", "do research on",
                    "study about", "academic search", "sources about",
                    "اقتراح مصادر", "بحث علمي", "أبحاث"],
        "research_deep": ["deep research", "بحث عميق", "comprehensive study",
                         "exhaustive search", "systematic review"],
        "source_import": ["import sources", "استيراد مصادر", "import bibtex",
                         "import zotero"],
        "citation_export": ["export citations", "تصدير الاستشهادات", "bibtex export"],
    }
```

### Handler Registration

```python
def register_handlers(wf_engine, cm):
    # ... Sprint 4 handlers ...

    if flags.is_enabled("research_provider"):
        from ..application.research_service import ResearchService
        svc = ResearchService(cm)
        wf_engine.register_handler("research", svc.execute)
        wf_engine.register_handler("research_quick", svc.execute_quick)
        wf_engine.register_handler("research_deep", svc.execute_deep)
```

---

## 17. Local First Design

### Principle

All research data lives in local SQLite. External APIs are optional enhancements, never required.

### Local Data

| Data | Location | Persistence |
|---|---|---|
| Source metadata | `research_sources` table | SQLite |
| Citations | `research_citations` table | SQLite |
| Dedup decisions | `research_dedup_log` table | SQLite |
| Research memories | `research_memory` table | SQLite |
| Full artifact content | `artifacts` table (content JSON) | SQLite |
| Rendered research reports | `data/artifacts/{id}/index.html` | Filesystem |
| Preview HTML/JSON | `data/artifacts/{id}/preview.html` | Filesystem |
| Cached provider results | `data/research/cache/{provider}/{hash}.json` | Filesystem |

### Offline Mode

When no providers are available (no API keys, no internet):
1. `WebResearcher` fails gracefully → returns cached sources
2. Local source library is still searchable
3. Citation engine works fully offline (generates citations from stored data)
4. Previous research artifacts are fully accessible
5. New sources can be added manually via import (BibTeX, RIS)

### Future Multi-User Path

The schema uses a single-user model. To multi-user:
1. Add `user_id TEXT NOT NULL` to `research_sources`, `research_citations`, `research_dedup_log`, `research_memory`
2. Add `user_id` to all indexes
3. Add a `user_id` filter to all queries
4. Scope artifact queries by `workspace_id` (already supported) or new `user_id`
5. The `WorkspaceState` already supports `user_id = "default"`

---

## 18. File Summary

| File | Action | Description |
|---|---|---|
| `toll/ports/research.py` | MODIFY | Expand ResearchProvider ABC, add `search_by_ids`, `is_available`, `supported_styles` |
| `toll/ports/research_source.py` | CREATE | ResearchSource, ResearchQuery, SourceType, CitationStyle enums |
| `toll/research/__init__.py` | CREATE | Package init |
| `toll/research/service.py` | CREATE | ResearchService orchestrator |
| `toll/research/source_manager.py` | CREATE | Source collection, dedup, ranking, tagging |
| `toll/research/citation_engine.py` | CREATE | Citation generation in 6 styles |
| `toll/research/dedup.py` | CREATE | 5-strategy deduplication |
| `toll/research/retention.py` | CREATE | Research retention policy |
| `toll/research/web_researcher.py` | CREATE | Fallback web-based research provider |
| `toll/adapters/research/__init__.py` | CREATE | Package init |
| `toll/adapters/research/notebooklm.py` | CREATE | NotebookLM adapter |
| `toll/adapters/research/semantic_scholar.py` | CREATE | Semantic Scholar adapter |
| `toll/adapters/research/google_scholar.py` | CREATE | Google Scholar scraper |
| `toll/adapters/research/arxiv.py` | CREATE | ArXiv API adapter |
| `toll/adapters/research/crossref.py` | CREATE | Crossref API adapter |
| `toll/adapters/research/zotero.py` | CREATE | Zotero API adapter |
| `toll/adapters/research/google_drive.py` | CREATE | Google Drive adapter |
| `toll/application/research_service.py` | CREATE | WorkflowEngine handler for research intents |
| `toll/application/handler_registry.py` | MODIFY | Register research handlers |
| `toll/workspace/manager.py` | MODIFY | Add `research_config` to workspace metadata |
| `toll/model/artifact.py` | MODIFY | Add `ArtifactType.RESEARCH` |
| `toll/model/migrations/0005_research.sql` | CREATE | 4 new tables: sources, citations, dedup_log, memory |
| `api/routers/research.py` | CREATE | Research API endpoints |
| `api/routers/artifacts.py` | MODIFY | Research-specific content/preview routes |
| `api/main.py` | MODIFY | Mount research router |
| `toll/core/feature_flags.py` | MODIFY | Add ~10 research feature flags |
| `toll/planner/planner.py` | MODIFY | Add research intents + keywords |
| `toll/context/engine.py` | MODIFY | Inject research memories into context |
| `toll/engine/renderers/preview_renderer.py` | MODIFY | Add `research_preview()` method |
| `docs/sprint5-design-review.md` | CREATE | This document |
