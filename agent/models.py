"""Modèle de données normalisé : un article scientifique trouvé par l'agent."""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict


def normalize_doi(doi: str | None) -> str:
    """'https://doi.org/10.1038/XYZ' -> '10.1038/xyz'"""
    if not doi:
        return ""
    doi = doi.strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.I)
    return doi.lower().rstrip(".")


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()


@dataclass
class Paper:
    doi: str = ""
    title: str = ""
    year: int | None = None
    journal: str = ""
    authors: list[str] = field(default_factory=list)
    cited_by_count: int | None = None
    is_oa: bool = False
    oa_url: str = ""
    url: str = ""
    abstract: str = ""
    openalex_id: str = ""
    arxiv_id: str = ""
    type_hint: str = ""            # "preprint" si arXiv/bioRxiv
    sample_size_hint: int | None = None   # taille d'échantillon connue (fixtures, extraction manuelle)
    sources: list[str] = field(default_factory=list)   # bases où l'article a été trouvé
    abstract_truncated: bool = False
    notes: str = ""

    @property
    def first_author(self) -> str:
        if not self.authors:
            return "anonyme"
        fam = self.authors[0].split(",")[-1].split()[-1] if "," in self.authors[0] else self.authors[0].split()[-1]
        return re.sub(r"[^A-Za-z]", "", fam).lower() or "anonyme"

    def merge(self, other: "Paper") -> None:
        """Fusionne un doublon (complète les champs manquants, union des sources)."""
        for f in ("doi", "title", "abstract", "journal", "oa_url", "url", "openalex_id", "arxiv_id"):
            if not getattr(self, f) and getattr(other, f):
                setattr(self, f, getattr(other, f))
        if self.year is None and other.year is not None:
            self.year = other.year
        if self.cited_by_count is None and other.cited_by_count is not None:
            self.cited_by_count = other.cited_by_count
        if not self.authors and other.authors:
            self.authors = other.authors
        if other.is_oa:
            self.is_oa = True
        if other.abstract_truncated is False and self.abstract_truncated:
            self.abstract_truncated = False
        for s in other.sources:
            if s not in self.sources:
                self.sources.append(s)

    def to_dict(self) -> dict:
        return asdict(self)


def deduplicate(papers: list[Paper]) -> list[Paper]:
    """Déduplique par DOI normalisé, sinon par titre normalisé. Fusionne les sources."""
    by_doi: dict[str, Paper] = {}
    by_title: dict[str, Paper] = {}
    result: list[Paper] = []
    for p in papers:
        key_doi = normalize_doi(p.doi)
        key_title = normalize_title(p.title)
        existing = None
        if key_doi and key_doi in by_doi:
            existing = by_doi[key_doi]
        elif key_title and key_title in by_title:
            existing = by_title[key_title]
        if existing is not None:
            existing.merge(p)
        else:
            result.append(p)
            if key_doi:
                by_doi[key_doi] = p
            if key_title:
                by_title[key_title] = p
    return result
