from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


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
    OTHER = "other"


class CitationStyle(str, Enum):
    APA = "apa"
    MLA = "mla"
    IEEE = "ieee"
    CHICAGO_NOTES = "chicago_notes"
    CHICAGO_DATE = "chicago_date"
    VANCOUVER = "vancouver"


class AccessType(str, Enum):
    OPEN = "open"
    RESTRICTED = "restricted"
    CLOSED = "closed"


@dataclass
class ResearchSource:
    id: str = ""
    title: str = ""
    url: str | None = None
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    citation: str = ""
    relevance_score: float = 0.0
    confidence_score: float = 0.0
    source_type: str | None = None
    doi: str | None = None
    journal: str | None = None
    abstract: str | None = None
    provider: str = ""
    provider_source_id: str | None = None
    citation_count: int = 0
    access_type: str = "open"
    language: str = "en"
    tags: list[str] = field(default_factory=list)
    in_library: bool = False
    publisher: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "authors": self.authors,
            "year": self.year,
            "citation": self.citation,
            "relevance_score": self.relevance_score,
            "confidence_score": self.confidence_score,
            "source_type": self.source_type,
            "doi": self.doi,
            "journal": self.journal,
            "abstract": self.abstract,
            "provider": self.provider,
            "provider_source_id": self.provider_source_id,
            "citation_count": self.citation_count,
            "access_type": self.access_type,
            "language": self.language,
            "tags": self.tags,
            "in_library": self.in_library,
            "publisher": self.publisher,
            "volume": self.volume,
            "issue": self.issue,
            "pages": self.pages,
        }


@dataclass
class ResearchQuery:
    query: str
    max_sources: int = 10
    style: str = "apa"
    include_full_text: bool = False
    providers: list[str] | None = None
    year_from: int | None = None
    year_to: int | None = None
    source_types: list[str] | None = None
    language: str | None = None


@dataclass
class ResearchResult:
    sources: list[ResearchSource] = field(default_factory=list)
    summary: str | None = None
    error: str | None = None
    provider: str = ""
