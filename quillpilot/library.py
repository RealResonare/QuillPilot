from __future__ import annotations

import re
import uuid
from pathlib import Path

from .bibtex import BibEntry, parse_bibtex_file
from .chunking import chunk_text
from .db import Database
from .models import CitationCandidate, ImportResponse, SearchResult
from .pdf import extract_pdf_text
from .search import OptionalChromaIndex, keyword_score, snippet, stable_id


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def citation_command(key: str, style: str = "cite") -> str:
    if style not in {"cite", "citep", "citet"}:
        raise ValueError("Unsupported citation style")
    if not re.match(r"^[A-Za-z0-9_:.\\/-]+$", key):
        raise ValueError("Invalid BibTeX key")
    return f"\\{style}{{{key}}}"


class LibraryService:
    def __init__(self, database: Database, vector_index: OptionalChromaIndex | None = None):
        self.database = database
        self.vector_index = vector_index

    def import_library(self, pdf_dir: str | None = None, bib_file: str | None = None) -> ImportResponse:
        warnings: list[str] = []
        bib_entries: list[BibEntry] = []
        if bib_file:
            bib_path = Path(bib_file).expanduser()
            if not bib_path.exists():
                raise FileNotFoundError(f"BibTeX file not found: {bib_path}")
            bib_entries = parse_bibtex_file(bib_path)
            self._upsert_bib_entries(bib_entries)

        pdf_paths: list[Path] = []
        if pdf_dir:
            root = Path(pdf_dir).expanduser()
            if not root.exists():
                raise FileNotFoundError(f"PDF directory not found: {root}")
            pdf_paths = sorted(root.glob("*.pdf"))

        papers_imported = 0
        chunks_indexed = 0
        for pdf_path in pdf_paths:
            try:
                extracted = extract_pdf_text(pdf_path)
            except Exception as exc:
                warnings.append(f"{pdf_path.name}: failed to parse PDF ({exc})")
                continue
            if not extracted.text:
                warnings.append(f"{pdf_path.name}: no extractable text; OCR is not supported in MVP")
                continue

            bib = self._match_bib_entry(pdf_path, extracted.title_hint)
            paper_id = self._upsert_paper(
                title=bib.title if bib and bib.title else extracted.title_hint,
                authors=bib.authors if bib else None,
                year=bib.year if bib else None,
                bibtex_key=bib.key if bib else None,
                pdf_path=pdf_path,
                doi=bib.doi if bib else None,
            )
            chunks = chunk_text(extracted.text)
            chunks_indexed += self._replace_chunks(
                paper_id=paper_id,
                title=bib.title if bib and bib.title else extracted.title_hint,
                authors=bib.authors if bib else None,
                bibtex_key=bib.key if bib else None,
                chunks=chunks,
            )
            papers_imported += 1

        return ImportResponse(
            papers_imported=papers_imported,
            bib_entries_imported=len(bib_entries),
            chunks_indexed=chunks_indexed,
            warnings=warnings,
        )

    def _upsert_bib_entries(self, entries: list[BibEntry]) -> None:
        with self.database.connect() as conn:
            conn.executemany(
                """
                INSERT INTO bib_entries (bibtex_key, entry_type, title, authors, year, doi, raw_bibtex)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(bibtex_key) DO UPDATE SET
                  entry_type=excluded.entry_type,
                  title=excluded.title,
                  authors=excluded.authors,
                  year=excluded.year,
                  doi=excluded.doi,
                  raw_bibtex=excluded.raw_bibtex,
                  updated_at=CURRENT_TIMESTAMP
                """,
                [(entry.key, entry.entry_type, entry.title, entry.authors, entry.year, entry.doi, entry.raw_bibtex) for entry in entries],
            )

    def _match_bib_entry(self, pdf_path: Path, title_hint: str) -> BibEntry | None:
        file_norm = _normalize(pdf_path.stem)
        title_norm = _normalize(title_hint)
        with self.database.connect() as conn:
            rows = conn.execute("SELECT * FROM bib_entries").fetchall()
        for row in rows:
            key = row["bibtex_key"]
            row_title = row["title"] or ""
            if _normalize(key) == file_norm:
                return BibEntry(key, row["entry_type"], row_title, row["authors"], row["year"], row["doi"], row["raw_bibtex"])
            normalized_title = _normalize(row_title)
            if normalized_title and (normalized_title in file_norm or normalized_title in title_norm):
                return BibEntry(key, row["entry_type"], row_title, row["authors"], row["year"], row["doi"], row["raw_bibtex"])
        return None

    def _upsert_paper(
        self,
        title: str,
        authors: str | None,
        year: str | None,
        bibtex_key: str | None,
        pdf_path: Path,
        doi: str | None,
    ) -> str:
        existing_id: str | None = None
        with self.database.connect() as conn:
            row = conn.execute("SELECT id FROM papers WHERE pdf_path = ?", (str(pdf_path.resolve()),)).fetchone()
            if row:
                existing_id = row["id"]
            paper_id = existing_id or str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO papers (id, title, authors, year, bibtex_key, pdf_path, doi)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(pdf_path) DO UPDATE SET
                  title=excluded.title,
                  authors=excluded.authors,
                  year=excluded.year,
                  bibtex_key=excluded.bibtex_key,
                  doi=excluded.doi,
                  updated_at=CURRENT_TIMESTAMP
                """,
                (paper_id, title, authors, year, bibtex_key, str(pdf_path.resolve()), doi),
            )
            return paper_id

    def _replace_chunks(self, paper_id: str, title: str, authors: str | None, bibtex_key: str | None, chunks) -> int:
        rows_for_vector: list[dict[str, str]] = []
        with self.database.connect() as conn:
            conn.execute("DELETE FROM chunks_fts WHERE paper_id = ?", (paper_id,))
            conn.execute("DELETE FROM chunks WHERE paper_id = ?", (paper_id,))
            for chunk in chunks:
                chunk_id = stable_id(paper_id, str(chunk.index), chunk.text[:100])
                conn.execute(
                    """
                    INSERT INTO chunks (id, paper_id, chunk_index, text, page_start, page_end)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (chunk_id, paper_id, chunk.index, chunk.text, chunk.page_start, chunk.page_end),
                )
                conn.execute(
                    """
                    INSERT INTO chunks_fts (chunk_id, paper_id, title, authors, bibtex_key, text)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (chunk_id, paper_id, title, authors, bibtex_key, chunk.text),
                )
                rows_for_vector.append(
                    {
                        "chunk_id": chunk_id,
                        "paper_id": paper_id,
                        "title": title,
                        "authors": authors or "",
                        "bibtex_key": bibtex_key or "",
                        "text": chunk.text,
                    }
                )
        if self.vector_index:
            self.vector_index.upsert_chunks(rows_for_vector)
        return len(rows_for_vector)

    def search(self, query: str, limit: int = 10, paper_ids: list[str] | None = None) -> list[SearchResult]:
        params: list[object] = []
        paper_filter = ""
        if paper_ids:
            paper_filter = " AND p.id IN (%s)" % ",".join("?" for _ in paper_ids)
            params.extend(paper_ids)

        with self.database.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT c.id AS chunk_id, p.id AS paper_id, p.title, p.authors, p.year, p.bibtex_key, c.text
                FROM chunks c
                JOIN papers p ON p.id = c.paper_id
                WHERE 1=1 {paper_filter}
                """,
                params,
            ).fetchall()

        ranked: list[SearchResult] = []
        for row in rows:
            score = keyword_score(query, row["title"], row["authors"], row["bibtex_key"], row["text"])
            if score <= 0:
                continue
            ranked.append(
                SearchResult(
                    paper_id=row["paper_id"],
                    chunk_id=row["chunk_id"],
                    title=row["title"],
                    authors=row["authors"],
                    year=row["year"],
                    bibtex_key=row["bibtex_key"],
                    snippet=snippet(row["text"], query),
                    score=round(score, 4),
                )
            )
        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:limit]

    def citation_candidates(
        self,
        query: str | None = None,
        paper_id: str | None = None,
        bibtex_key: str | None = None,
        limit: int = 5,
    ) -> list[CitationCandidate]:
        with self.database.connect() as conn:
            if bibtex_key:
                rows = conn.execute(
                    """
                    SELECT p.id AS paper_id, b.bibtex_key, b.title, b.authors, b.year
                    FROM bib_entries b
                    LEFT JOIN papers p ON p.bibtex_key = b.bibtex_key
                    WHERE b.bibtex_key = ?
                    """,
                    (bibtex_key,),
                ).fetchall()
            elif paper_id:
                rows = conn.execute(
                    """
                    SELECT p.id AS paper_id, b.bibtex_key, COALESCE(b.title, p.title) AS title,
                           COALESCE(b.authors, p.authors) AS authors, COALESCE(b.year, p.year) AS year
                    FROM papers p
                    JOIN bib_entries b ON b.bibtex_key = p.bibtex_key
                    WHERE p.id = ?
                    """,
                    (paper_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT p.id AS paper_id, b.bibtex_key, b.title, b.authors, b.year
                    FROM bib_entries b
                    LEFT JOIN papers p ON p.bibtex_key = b.bibtex_key
                    """
                ).fetchall()

        candidates = [
            CitationCandidate(
                paper_id=row["paper_id"],
                bibtex_key=row["bibtex_key"],
                title=row["title"],
                authors=row["authors"],
                year=row["year"],
            )
            for row in rows
        ]
        if query and not (paper_id or bibtex_key):
            candidates.sort(
                key=lambda item: keyword_score(query, item.title, item.authors, item.year, item.bibtex_key),
                reverse=True,
            )
            candidates = [item for item in candidates if keyword_score(query, item.title, item.authors, item.year, item.bibtex_key) > 0]
        return candidates[:limit]
