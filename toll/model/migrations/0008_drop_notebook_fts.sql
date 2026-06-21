-- Remove unused FTS5 index on notebook_notes.
-- The index was write-only (never queried) and had broken rowid linkage
-- with the TEXT primary key. Queries use AI, not full-text search.

DROP TABLE IF EXISTS notebook_notes_fts;
