from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from ..core.connection_manager import ConnectionManager
from ..ports.research_source import ResearchQuery, ResearchSource, SourceType
from .citation_engine import CitationEngine
from .dedup import DedupEngine


class SourceManager:
    def __init__(
        self,
        cm: ConnectionManager | None = None,
        citation_engine: CitationEngine | None = None,
        dedup_engine: DedupEngine | None = None,
    ):
        self.cm = cm
        self.citation_engine = citation_engine or CitationEngine()
        self.dedup_engine = dedup_engine or DedupEngine(cm=cm)

    def store(
        self,
        source: ResearchSource,
        artifact_id: str | None = None,
    ) -> ResearchSource:
        if not self.cm:
            return source
        now = datetime.now(timezone.utc).isoformat()
        source_id = source.id or str(uuid.uuid4())
        source.id = source_id
        self.cm.execute(
            """INSERT INTO research_sources
               (id, artifact_id, title, authors, year, journal, doi, url, abstract,
                source_type, provider, provider_source_id, citation_count,
                relevance_score, confidence_score, access_type, language, tags,
                metadata, citation, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                source_id,
                artifact_id,
                source.title,
                json.dumps(source.authors, ensure_ascii=False),
                source.year,
                source.journal,
                source.doi,
                source.url,
                source.abstract,
                source.source_type or "web",
                source.provider,
                source.provider_source_id,
                source.citation_count,
                source.relevance_score,
                source.confidence_score,
                source.access_type,
                source.language,
                json.dumps(source.tags, ensure_ascii=False),
                "{}",
                source.citation,
                now,
                now,
            ),
        )
        self.cm.commit()
        source.in_library = True
        return source

    def get(self, source_id: str) -> ResearchSource | None:
        if not self.cm:
            return None
        row = self.cm.connection.execute(
            "SELECT * FROM research_sources WHERE id = ?", (source_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_source(row)

    def list(
        self,
        artifact_id: str | None = None,
        provider: str | None = None,
        source_type: str | None = None,
        limit: int = 100,
    ) -> list[ResearchSource]:
        if not self.cm:
            return []
        parts = ["SELECT * FROM research_sources WHERE 1=1"]
        params: list[Any] = []
        if artifact_id:
            parts.append("AND artifact_id = ?")
            params.append(artifact_id)
        if provider:
            parts.append("AND provider = ?")
            params.append(provider)
        if source_type:
            parts.append("AND source_type = ?")
            params.append(source_type)
        parts.append("ORDER BY relevance_score DESC LIMIT ?")
        params.append(limit)
        rows = self.cm.connection.execute(
            " ".join(parts), params
        ).fetchall()
        return [self._row_to_source(r) for r in rows]

    def update_source_id(
        self, old_id: str | None, new_id: str
    ):
        if not old_id or not self.cm:
            return
        self.cm.execute(
            "UPDATE research_sources SET artifact_id = ? WHERE id = ?",
            (new_id, old_id),
        )
        self.cm.commit()

    def delete_source(self, source_id: str) -> bool:
        if not self.cm:
            return False
        cursor = self.cm.execute(
            "DELETE FROM research_sources WHERE id = ?",
            (source_id,),
        )
        self.cm.commit()
        return cursor.rowcount > 0

    def add_tags(self, source_id: str, tags: list[str]):
        if not self.cm:
            return
        source = self.get(source_id)
        if not source:
            return
        existing = set(source.tags)
        merged = list(existing | set(tags))
        self.cm.execute(
            "UPDATE research_sources SET tags = ?, updated_at = ? WHERE id = ?",
            (json.dumps(merged, ensure_ascii=False),
             datetime.now(timezone.utc).isoformat(), source_id),
        )
        self.cm.commit()

    def collect(
        self,
        query: ResearchQuery,
        providers: list[Any],
    ) -> list[ResearchSource]:
        all_sources: list[ResearchSource] = []
        for provider in providers:
            if not provider.is_available():
                continue
            try:
                result = provider.search(query)
                for src in result.sources:
                    src.provider = provider.name
                all_sources.extend(result.sources)
            except Exception:
                continue

        deduped = self.dedup_engine.deduplicate(all_sources)
        self._rank(deduped)
        return deduped[: query.max_sources]

    def import_bibtex(self, content: str) -> list[ResearchSource]:
        sources: list[ResearchSource] = []
        entries = re.findall(
            r"@(\w+)\s*\{\s*([^,]+)\s*,(.*?)\n\}", content, re.DOTALL
        )
        for entry_type, key, fields_text in entries:
            fields = dict(
                re.findall(
                    r"\s*(\w+)\s*=\s*\{(.+?)\}", fields_text, re.DOTALL
                )
            )
            authors_raw = fields.get("author", "")
            authors = [
                a.strip()
                for a in re.split(r"\s+and\s+", authors_raw)
                if a.strip()
            ]
            year_raw = fields.get("year", "")
            year = int(year_raw) if year_raw.isdigit() else None
            source = ResearchSource(
                title=fields.get("title", "").strip().rstrip("."),
                authors=authors,
                year=year,
                doi=fields.get("doi"),
                url=fields.get("url"),
                journal=fields.get("journal"),
                publisher=fields.get("publisher"),
                volume=fields.get("volume"),
                pages=fields.get("pages"),
                source_type=self._bibtex_to_source_type(entry_type),
                provider="bibtex_import",
            )
            sources.append(source)
        return sources

    def import_ris(self, content: str) -> list[ResearchSource]:
        sources: list[ResearchSource] = []
        records = re.split(r"\n\s*ER\s*-", content, flags=re.IGNORECASE)
        for record in records:
            if not record.strip():
                continue
            fields: dict[str, list[str]] = {}
            for line in record.strip().split("\n"):
                line = line.strip()
                m = re.match(r"([A-Z][A-Z0-9]?)\s*-\s*(.*)", line)
                if m:
                    tag = m.group(1).upper()
                    value = m.group(2).strip()
                    fields.setdefault(tag, []).append(value)
            authors = fields.get("AU", [])
            year_raw = fields.get("PY", [""])[0]
            year = (
                int(year_raw[:4])
                if year_raw and year_raw[:4].isdigit()
                else None
            )
            source = ResearchSource(
                title=fields.get("TI", fields.get("T1", [""]))[0],
                authors=authors,
                year=year,
                doi=fields.get("DO", [None])[0],
                url=fields.get("UR", [None])[0],
                journal=fields.get("JO", [None])[0],
                publisher=fields.get("PB", [None])[0],
                volume=fields.get("VL", [None])[0],
                pages=fields.get("SP", [None])[0],
                source_type=self._ris_to_source_type(
                    fields.get("TY", [None])[0]
                ),
                provider="ris_import",
            )
            sources.append(source)
        return sources

    def _bibtex_to_source_type(self, entry_type: str) -> str:
        mapping = {
            "article": "journal",
            "book": "book",
            "incollection": "book_chapter",
            "inproceedings": "conference",
            "phdthesis": "thesis",
            "techreport": "report",
            "misc": "preprint",
        }
        return mapping.get(entry_type.lower(), "other")

    def _ris_to_source_type(self, ris_type: str | None) -> str:
        mapping = {
            "JOUR": "journal",
            "BOOK": "book",
            "CHAP": "book_chapter",
            "CONF": "conference",
            "THES": "thesis",
            "RPT": "report",
            "GEN": "preprint",
        }
        return mapping.get(ris_type or "", "other")

    def _rank(self, sources: list[ResearchSource]):
        sources.sort(
            key=lambda s: (
                s.relevance_score * 0.4
                + s.confidence_score * 0.3
                + min(s.citation_count / 100, 1.0) * 0.2
                + (0.1 if s.doi else 0.0)
            ),
            reverse=True,
        )

    def _row_to_source(self, row) -> ResearchSource:
        row_dict = dict(row) if hasattr(row, "keys") else row
        return ResearchSource(
            id=row_dict.get("id", ""),
            title=row_dict["title"],
            url=row_dict["url"],
            authors=json.loads(row_dict["authors"]) if row_dict.get("authors") else [],
            year=row_dict["year"],
            citation=row_dict.get("citation") or "",
            relevance_score=row_dict.get("relevance_score") or 0.0,
            confidence_score=row_dict.get("confidence_score") or 0.0,
            source_type=row_dict["source_type"],
            doi=row_dict.get("doi"),
            journal=row_dict.get("journal"),
            abstract=row_dict.get("abstract"),
            provider=row_dict["provider"],
            provider_source_id=row_dict.get("provider_source_id"),
            citation_count=row_dict.get("citation_count") or 0,
            access_type=row_dict.get("access_type") or "open",
            language=row_dict.get("language") or "en",
            tags=json.loads(row_dict["tags"]) if row_dict.get("tags") else [],
            in_library=True,
            publisher=row_dict.get("publisher"),
            volume=row_dict.get("volume"),
            issue=row_dict.get("issue"),
            pages=row_dict.get("pages"),
        )
