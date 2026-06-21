CREATE TABLE IF NOT EXISTS research_sources (
    id TEXT PRIMARY KEY,
    artifact_id TEXT,
    title TEXT NOT NULL,
    authors TEXT DEFAULT '[]',
    year INTEGER,
    journal TEXT,
    doi TEXT,
    url TEXT,
    abstract TEXT,
    source_type TEXT NOT NULL DEFAULT 'web',
    provider TEXT NOT NULL DEFAULT '',
    provider_source_id TEXT,
    citation_count INTEGER DEFAULT 0,
    relevance_score REAL DEFAULT 0.0,
    confidence_score REAL DEFAULT 0.0,
    access_type TEXT DEFAULT 'open',
    language TEXT DEFAULT 'en',
    publisher TEXT,
    volume TEXT,
    issue TEXT,
    pages TEXT,
    tags TEXT DEFAULT '[]',
    metadata TEXT DEFAULT '{}',
    citation TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (artifact_id) REFERENCES artifacts(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS research_citations (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    artifact_id TEXT,
    style TEXT NOT NULL DEFAULT 'apa',
    citation TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES research_sources(id) ON DELETE CASCADE,
    FOREIGN KEY (artifact_id) REFERENCES artifacts(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS research_dedup_log (
    id TEXT PRIMARY KEY,
    source_a_id TEXT NOT NULL,
    source_b_id TEXT NOT NULL,
    strategy TEXT NOT NULL,
    similarity_score REAL NOT NULL,
    merged_into TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_research_sources_artifact ON research_sources(artifact_id);
CREATE INDEX IF NOT EXISTS idx_research_sources_provider ON research_sources(provider);
CREATE INDEX IF NOT EXISTS idx_research_sources_doi ON research_sources(doi);
CREATE INDEX IF NOT EXISTS idx_research_sources_type ON research_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_research_citations_source ON research_citations(source_id);
CREATE INDEX IF NOT EXISTS idx_research_citations_style ON research_citations(style);
CREATE INDEX IF NOT EXISTS idx_research_dedup_merged ON research_dedup_log(merged_into);
