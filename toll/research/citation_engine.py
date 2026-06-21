from __future__ import annotations

import re
from typing import Any

from ..ports.research_source import CitationStyle, ResearchSource


class CitationEngine:
    def format(self, source: ResearchSource, style: str = "apa") -> str:
        try:
            style_enum = CitationStyle(style)
        except ValueError:
            style_enum = CitationStyle.APA
        if style_enum == CitationStyle.APA:
            return self._format_apa(source)
        if style_enum == CitationStyle.MLA:
            return self._format_mla(source)
        if style_enum == CitationStyle.IEEE:
            return self._format_ieee(source)
        if style_enum == CitationStyle.CHICAGO_NOTES:
            return self._format_chicago_notes(source)
        if style_enum == CitationStyle.CHICAGO_DATE:
            return self._format_chicago_date(source)
        if style_enum == CitationStyle.VANCOUVER:
            return self._format_vancouver(source)
        return self._format_apa(source)

    def format_batch(
        self, sources: list[ResearchSource], style: str = "apa"
    ) -> list[str]:
        return [self.format(s, style) for s in sources]

    def _author_last_first(self, author: str) -> str:
        parts = re.split(r",\s*", author.strip(), maxsplit=1)
        if len(parts) == 2:
            return f"{parts[1]} {parts[0]}"
        return author

    def _author_first_initial(self, author: str) -> str:
        parts = re.split(r",\s*", author.strip(), maxsplit=1)
        if len(parts) == 2:
            initials = "".join(
                f"{p[0]}." for p in parts[1].split() if p
            )
            return f"{parts[0]}, {initials}"
        name_parts = author.strip().split()
        if len(name_parts) >= 2:
            last = name_parts[-1]
            initials = "".join(f"{p[0]}." for p in name_parts[:-1] if p)
            return f"{last}, {initials}"
        return author

    def _author_initials_last(self, author: str) -> str:
        parts = re.split(r",\s*", author.strip(), maxsplit=1)
        if len(parts) == 2:
            initials = "".join(f"{p[0]}." for p in parts[1].split() if p)
            return f"{initials} {parts[0]}"
        name_parts = author.strip().split()
        if len(name_parts) >= 2:
            last = name_parts[-1]
            initials = "".join(f"{p[0]}." for p in name_parts[:-1] if p)
            return f"{initials} {last}"
        return author

    def _author_last_only(self, author: str) -> str:
        parts = re.split(r",\s*", author.strip(), maxsplit=1)
        if len(parts) == 2:
            return parts[0]
        name_parts = author.strip().split()
        return name_parts[-1] if name_parts else author

    def _format_authors_ampersand(self, authors: list[str]) -> str:
        if not authors:
            return ""
        if len(authors) == 1:
            return self._author_last_first(authors[0])
        if len(authors) == 2:
            return (
                f"{self._author_last_first(authors[0])} & "
                f"{self._author_last_first(authors[1])}"
            )
        return (
            ", ".join(self._author_last_first(a) for a in authors[:-1])
            + f", & {self._author_last_first(authors[-1])}"
        )

    def _format_authors_ampersand_initials(
        self, authors: list[str]
    ) -> str:
        if not authors:
            return ""
        if len(authors) == 1:
            return self._author_first_initial(authors[0])
        if len(authors) == 2:
            return (
                f"{self._author_first_initial(authors[0])} & "
                f"{self._author_first_initial(authors[1])}"
            )
        return (
            ", ".join(
                self._author_first_initial(a) for a in authors[:-1]
            )
            + f", & {self._author_first_initial(authors[-1])}"
        )

    def _format_authors_initials_last(
        self, authors: list[str]
    ) -> str:
        if not authors:
            return ""
        return ", ".join(
            self._author_initials_last(a) for a in authors
        )

    def _format_authors_comma_and(self, authors: list[str]) -> str:
        if not authors:
            return ""
        if len(authors) == 1:
            return self._author_last_first(authors[0])
        if len(authors) == 2:
            return (
                f"{self._author_last_first(authors[0])} and "
                f"{self._author_last_first(authors[1])}"
            )
        return (
            ", ".join(self._author_last_first(a) for a in authors[:-1])
            + f", and {self._author_last_first(authors[-1])}"
        )

    def _format_apa(self, source: ResearchSource) -> str:
        author_str = self._format_authors_ampersand_initials(
            source.authors
        )
        year = source.year or "n.d."
        title = source.title
        parts = [f"{author_str} ({year}). {title}."] if author_str else [f"{title}. ({year})."]
        if source.source_type in ("journal", None) and source.journal:
            parts[0] = parts[0].rstrip(".")
            journal_part = f"*{source.journal}*"
            vol_issue = ""
            if source.volume:
                vol_issue = source.volume
                if source.issue:
                    vol_issue += f"({source.issue})"
            if vol_issue:
                journal_part += f", {vol_issue}"
            if source.pages:
                journal_part += f", {source.pages}"
            parts[0] += f". {journal_part}"
            if source.doi:
                parts[0] += f". https://doi.org/{source.doi}"
            elif source.url:
                parts[0] += f". {source.url}"
        elif source.doi:
            parts[0] += f" https://doi.org/{source.doi}"
        elif source.url:
            parts[0] += f" {source.url}"
        return parts[0]

    def _format_mla(self, source: ResearchSource) -> str:
        author_str = (
            ", et al.".join(
                [
                    self._author_last_first(source.authors[0]),
                    ""
                ]
            )
            if len(source.authors) > 3
            else self._format_authors_comma_and(source.authors)
        ) if source.authors else ""
        title = f'"{source.title}."'
        parts = [f"{author_str} {title}"] if author_str else [title]
        if source.journal:
            parts[0] += f" *{source.journal}*,"
            parts[0] += f" vol. {source.volume}" if source.volume else ""
            parts[0] += f", {source.year}" if source.year else ""
        elif source.year:
            parts[0] += f" {source.year},"
        if source.doi:
            parts[0] += f" doi:{source.doi}."
        elif source.url:
            parts[0] += f" {source.url}."
        return parts[0]

    def _format_ieee(self, source: ResearchSource) -> str:
        author_str = self._format_authors_initials_last(source.authors)
        title = f'"{source.title},'
        parts = [f"{author_str}, {title}"] if author_str else [title]
        if source.journal:
            parts[0] += f" *{source.journal}*,"
            if source.volume:
                parts[0] += f" vol. {source.volume},"
        parts[0] += f" {source.year}." if source.year else "."
        if source.doi:
            parts[0] += f" doi: {source.doi}."
        return parts[0]

    def _format_chicago_notes(self, source: ResearchSource) -> str:
        author_str = (
            self._format_authors_comma_and(source.authors)
            if source.authors
            else ""
        )
        title = f'"{source.title}."'
        parts = [f"{author_str}. {title}"] if author_str else [title]
        if source.journal:
            parts[0] += f" *{source.journal}*"
            if source.volume:
                vol_part = source.volume
                if source.issue:
                    vol_part += f", no. {source.issue}"
                parts[0] += f" {vol_part}"
            parts[0] += f" ({source.year})" if source.year else ""
        elif source.publisher:
            parts[0] += f" {source.publisher}."
            if source.year:
                parts[0] += f" ({source.year})."
        elif source.year:
            parts[0] += f" ({source.year})."
        if source.doi:
            parts[0] += f". https://doi.org/{source.doi}"
        elif source.url:
            parts[0] += f". {source.url}"
        return parts[0]

    def _format_chicago_date(self, source: ResearchSource) -> str:
        author_str = (
            self._author_last_first(source.authors[0])
            if len(source.authors) == 1
            else (
                f"{self._author_last_first(source.authors[0])} and "
                f"{self._author_last_first(source.authors[1])}"
            )
        ) if source.authors else ""
        parts = []
        if author_str:
            year_str = f"{source.year}. " if source.year else "n.d. "
            parts.append(f"{author_str}. {year_str}")
        else:
            parts.append("")
        parts[0] += f'"{source.title}."'
        if source.journal:
            parts[0] += f" *{source.journal}*"
            if source.volume:
                vol_part = source.volume
                if source.issue:
                    vol_part += f", no. {source.issue}"
                parts[0] += f" {vol_part}"
        elif source.year and not author_str:
            parts[0] += f" ({source.year})."
        if source.doi:
            parts[0] += f". https://doi.org/{source.doi}"
        elif source.url:
            parts[0] += f". {source.url}"
        return parts[0]

    def _format_vancouver(self, source: ResearchSource) -> str:
        author_str = ", ".join(
            self._author_last_only(a) for a in source.authors
        )
        title = source.title
        parts = []
        if author_str:
            parts.append(f"{author_str}. {title}.")
        else:
            parts.append(f"{title}.")
        if source.journal:
            parts[0] += f" {source.journal}."
        parts[0] += f" {source.year}"
        if source.volume:
            parts[0] += f";{source.volume}({source.issue or '?'})"
        parts[0] += "."
        if source.doi:
            parts[0] += f" DOI: {source.doi}."
        return parts[0]

    def export_bibtex(self, sources: list[ResearchSource]) -> str:
        entries = []
        for i, source in enumerate(sources):
            key = f"{self._bibtex_key(source, i)}"
            entries.append(self._bibtex_entry(source, key))
        return "\n\n".join(entries)

    def _bibtex_key(self, source: ResearchSource, idx: int) -> str:
        author_part = (
            source.authors[0].split(",")[0].strip().lower()
            if source.authors
            else "unknown"
        )
        year_part = str(source.year) if source.year else "nodate"
        return f"{author_part}{year_part}{idx}"

    def _bibtex_entry(self, source: ResearchSource, key: str) -> str:
        entry_type = self._bibtex_type(source.source_type)
        lines = [f"@{entry_type}{{{key},"]
        fields = {
            "author": " and ".join(
                self._author_last_first(a) for a in source.authors
            ),
            "title": source.title,
            "year": str(source.year) if source.year else None,
            "journal": source.journal,
            "volume": source.volume,
            "doi": source.doi,
            "url": source.url,
        }
        for field, value in fields.items():
            if value:
                lines.append(f"  {field} = {{{value}}},")
        lines.append("}")
        return "\n".join(lines)

    def _bibtex_type(self, source_type: str | None) -> str:
        mapping = {
            "journal": "article",
            "book": "book",
            "book_chapter": "incollection",
            "conference": "inproceedings",
            "thesis": "phdthesis",
            "report": "techreport",
            "preprint": "misc",
            "web": "misc",
            "dataset": "misc",
        }
        return mapping.get(source_type or "", "misc")

    def export_ris(self, sources: list[ResearchSource]) -> str:
        entries = []
        for source in sources:
            entries.append(self._ris_entry(source))
        return "\n\n".join(entries)

    def _ris_entry(self, source: ResearchSource) -> str:
        ris_type = self._ris_type(source.source_type)
        lines = [f"TY  - {ris_type}"]
        for author in source.authors:
            lines.append(f"AU  - {author}")
        lines.append(f"TI  - {source.title}")
        if source.journal:
            lines.append(f"JO  - {source.journal}")
        if source.year:
            lines.append(f"PY  - {source.year}")
        if source.doi:
            lines.append(f"DO  - {source.doi}")
        if source.url:
            lines.append(f"UR  - {source.url}")
        if source.abstract:
            lines.append(f"AB  - {source.abstract}")
        if source.citation_count:
            lines.append(f"VL  - {source.citation_count}")
        lines.append("ER  - ")
        return "\n".join(lines)

    def _ris_type(self, source_type: str | None) -> str:
        mapping = {
            "journal": "JOUR",
            "book": "BOOK",
            "book_chapter": "CHAP",
            "conference": "CONF",
            "thesis": "THES",
            "report": "RPT",
            "preprint": "GEN",
            "web": "GEN",
        }
        return mapping.get(source_type or "", "GEN")
