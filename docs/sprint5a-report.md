# Sprint 5A — Research Layer Foundation

**Status**: ✅ Complete  
**Tests**: 170 passed, 0 failed, 2 skipped  
**New tests**: 43 (research module)  
**New modules**: 10 files across ports, research, adapters, application, api, migrations

---

## Delivered

### 1. Ports & Models
| File | What |
|------|------|
| `toll/ports/research.py` | `ResearchProvider` ABC expanded with `search_by_ids()`, `is_available()`, `rate_limit_remaining()`, `supported_styles`, `max_sources_per_query` |
| `toll/ports/research_source.py` | `ResearchSource` (18 fields + `confidence_score` + `publisher`/`volume`/`issue`/`pages`), `ResearchQuery`, `ResearchResult`, `SourceType`, `CitationStyle`, `AccessType` enums |
| `toll/model/artifact.py` | `ArtifactType.RESEARCH` added |
| `toll/model/migrations/0005_research.sql` | 3 tables (`research_sources`, `research_citations`, `research_dedup_log`) + 7 indexes |

### 2. Research Core
| File | What |
|------|------|
| `toll/research/citation_engine.py` | `CitationEngine` — 6 style formatters (APA, MLA, IEEE, Chicago Notes, Chicago Date, Vancouver) + `format_batch()`, `export_bibtex()`, `export_ris()` |
| `toll/research/dedup.py` | `DedupEngine` — 5 strategies (DOI, URL, title/Levenshtein, author+year composite, content hash), Union-Find merge, DB logging |
| `toll/research/source_manager.py` | `SourceManager` — `collect()`, `store()`, `get()`, `list()`, `delete_source()`, `add_tags()`, `import_bibtex()`, `import_ris()`, weighted ranking formula |
| `toll/research/web_researcher.py` | `WebResearcher` — fallback DuckDuckGo-based research provider implementating `ResearchProvider` |

### 3. Application Layer
| File | What |
|------|------|
| `toll/application/research_service.py` | `ResearchService` — workflow handler with `execute()` (full research), `execute_quick()` (lightweight), `execute_deep()` (full research) |
| `toll/application/handler_registry.py` | Registered `research`, `research_quick`, `research_deep` handlers, gated by `research_provider` flag |
| `toll/engine/renderers/preview_renderer.py` | `research_preview()` method — RTL Arabic research artifact preview |

### 4. Infrastructure
| File | What |
|------|------|
| `toll/adapters/research/google_drive.py` | `GoogleDriveAdapter` — Phase 1: backup artifact files + metadata to local `drive_backup/` directory |
| `api/routers/research.py` | Research API — `POST /api/research`, `GET /api/research/styles`, `GET /api/research/modes` |
| `api/main.py` | Mounted research router |
| `toll/planner/planner.py` | Added `research` (requires approval), `research_quick` (auto), `research_deep` (approval) intents + keywords |
| `toll/core/feature_flags.py` | 10 research flags + `google_drive_backup` |

### 5. Feature Flags (Sprint 5A defaults)
| Flag | Default | Purpose |
|------|---------|---------|
| `research_provider` | ✅ enabled | Enables research workflow handlers |
| `citation_engine` | ✅ enabled | Enables citation formatting |
| `source_dedup` | ✅ enabled | Enables source deduplication |
| `research_deep` | ❌ disabled | Deep research mode |
| `google_drive_backup` | ❌ disabled | Google Drive backup (Phase 1) |
| `*_provider` flags | ❌ disabled | External provider toggles (semantic_scholar, google_scholar, arxiv, crossref, zotero) |

---

## Architecture

```
User Request → Planner → WorkflowEngine → ResearchService
                                              │
                                ┌─────────────┼─────────────┐
                                ▼             ▼             ▼
                         SourceManager   CitationEngine  AI Synthesis
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
              DedupEngine  WebResearcher  External APIs
                                         (future)
```

**Source ranking formula**: `relevance_score × 0.4 + confidence_score × 0.3 + citation_count_norm × 0.2 + doi_exists × 0.1`

**Dedup strategy order**: DOI (1.0) → URL (1.0) → title/Levenshtein (0.85) → author+year (0.95) → content hash (1.0)

---

## REST API

```http
POST /api/research
{
  "topic": "الذكاء الاصطناعي في التعليم",
  "style": "apa",
  "max_sources": 10,
  "mode": "standard"
}
# → { "artifact_id": "...", "source_count": 5, "citation_count": 5, ... }

GET /api/research/styles
# → { "styles": [{"id": "apa", "label": "APA (7th ed.)"}, ...] }

GET /api/research/modes
# → { "modes": [{"id": "standard", ...}, {"id": "quick", ...}, {"id": "deep", ...}] }
```

## Deferred to Sprint 5B
- NotebookLM integration
- Research memory & semester-aware workflows
- Google Drive sync (bidirectional)
- External provider adapters (Semantic Scholar, Google Scholar, arXiv, Crossref, Zotero)
- Advanced citation analytics
