from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from .bibtex import BibEntry, parse_bibtex_file
from .chunking import chunk_text
from .db import Database
from .models import CitationCandidate, ImportRequest, ImportResponse, ImportTaskResponse, LibraryStats, SearchResult
from .pdf import extract_pdf_text
from .search import OptionalChromaIndex, keyword_score, snippet, stable_id


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _words(value: str | None) -> set[str]:
    return {word.lower() for word in re.findall(r"[A-Za-z0-9]+", value or "")}


def _fts_query(value: str) -> str:
    terms = re.findall(r"[\w-]+", value, flags=re.UNICODE)
    quoted_terms = []
    for term in terms:
        escaped = term.replace('"', '""')
        quoted_terms.append(f'"{escaped}"')
    return " OR ".join(quoted_terms)


def citation_command(key: str, style: str = "cite") -> str:
    if style not in {"cite", "citep", "citet"}:
        raise ValueError("Unsupported citation style")
    if not re.match(r"^[A-Za-z0-9_:.\\/-]+$", key):
        raise ValueError("Invalid BibTeX key")
    return f"\\{style}{{{key}}}"


def citation_rank(query: str | None, candidate: CitationCandidate) -> tuple[float, str]:
    if not query:
        return 1.0, "Imported BibTeX key"

    query_norm = _normalize(query)
    key_norm = _normalize(candidate.bibtex_key)
    title_norm = _normalize(candidate.title)
    query_words = _words(query)
    author_words = _words(candidate.authors)

    if query_norm and query_norm == key_norm:
        return 100.0, "Exact BibTeX key match"
    if query_norm and title_norm and query_norm == title_norm:
        return 90.0, "Title match"
    if query_norm and title_norm and (query_norm in title_norm or title_norm in query_norm):
        return 80.0, "Title contains query"
    if query_words and author_words and query_words.intersection(author_words):
        return 70.0 + len(query_words.intersection(author_words)), "Author match"
    if candidate.year and candidate.year in query:
        return 60.0, "Year match"

    score = keyword_score(query, candidate.title, candidate.authors, candidate.year, candidate.bibtex_key)
    if score > 0:
        return round(10.0 + score, 4), "Keyword match"
    return 0.0, "No match"


@dataclass(frozen=True)
class UpsertPaperResult:
    paper_id: str
    duplicate_reason: str | None = None


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
            upserted = self._upsert_paper(
                title=bib.title if bib and bib.title else extracted.title_hint,
                authors=bib.authors if bib else None,
                year=bib.year if bib else None,
                bibtex_key=bib.key if bib else None,
                pdf_path=pdf_path,
                doi=bib.doi if bib else None,
            )
            if upserted.duplicate_reason:
                warnings.append(f"{pdf_path.name}: matched existing paper by {upserted.duplicate_reason}")
            chunks = chunk_text(extracted.text)
            chunks_indexed += self._replace_chunks(
                paper_id=upserted.paper_id,
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

    def create_import_task(self, request: ImportRequest) -> ImportTaskResponse:
        task_id = str(uuid.uuid4())
        detail = json.dumps({"pdf_dir": request.pdf_dir, "bib_file": request.bib_file, "result": None, "warnings": []})
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks (id, kind, status, detail)
                VALUES (?, 'import', 'queued', ?)
                """,
                (task_id, detail),
            )
        return self.get_task(task_id)

    def run_import_task(self, task_id: str, request: ImportRequest) -> None:
        self._update_task(task_id, "running", {"pdf_dir": request.pdf_dir, "bib_file": request.bib_file, "result": None, "warnings": []})
        try:
            result = self.import_library(pdf_dir=request.pdf_dir, bib_file=request.bib_file)
        except Exception as exc:
            self._update_task(
                task_id,
                "failed",
                {"pdf_dir": request.pdf_dir, "bib_file": request.bib_file, "result": None, "warnings": [str(exc)]},
            )
            return
        self._update_task(
            task_id,
            "completed",
            {
                "pdf_dir": request.pdf_dir,
                "bib_file": request.bib_file,
                "result": result.model_dump(),
                "warnings": result.warnings,
            },
        )

    def get_task(self, task_id: str) -> ImportTaskResponse:
        with self.database.connect() as conn:
            row = conn.execute("SELECT id, status, detail FROM tasks WHERE id = ? AND kind = 'import'", (task_id,)).fetchone()
        if not row:
            raise KeyError(task_id)
        detail_payload = json.loads(row["detail"] or "{}")
        result_payload = detail_payload.get("result")
        return ImportTaskResponse(
            task_id=row["id"],
            status=row["status"],
            detail=row["detail"],
            result=ImportResponse.model_validate(result_payload) if result_payload else None,
            warnings=list(detail_payload.get("warnings") or []),
        )

    def stats(self) -> LibraryStats:
        with self.database.connect() as conn:
            papers_count = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
            bib_entries_count = conn.execute("SELECT COUNT(*) FROM bib_entries").fetchone()[0]
            chunks_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            latest_task = conn.execute(
                """
                SELECT status, updated_at
                FROM tasks
                WHERE kind = 'import'
                ORDER BY updated_at DESC
                LIMIT 1
                """
            ).fetchone()
            latest_completed = conn.execute(
                """
                SELECT updated_at
                FROM tasks
                WHERE kind = 'import' AND status = 'completed'
                ORDER BY updated_at DESC
                LIMIT 1
                """
            ).fetchone()
        return LibraryStats(
            papers_count=papers_count,
            bib_entries_count=bib_entries_count,
            chunks_count=chunks_count,
            latest_import_at=latest_completed["updated_at"] if latest_completed else None,
            latest_task_status=latest_task["status"] if latest_task else None,
        )

    def _update_task(self, task_id: str, status: str, detail: dict[str, object]) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET status = ?, detail = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, json.dumps(detail), task_id),
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
    ) -> UpsertPaperResult:
        existing_id: str | None = None
        duplicate_reason: str | None = None
        resolved_pdf_path = str(pdf_path.resolve())
        with self.database.connect() as conn:
            row = conn.execute("SELECT id FROM papers WHERE pdf_path = ?", (resolved_pdf_path,)).fetchone()
            if row:
                existing_id = row["id"]
            if not existing_id and bibtex_key:
                row = conn.execute("SELECT id FROM papers WHERE bibtex_key = ?", (bibtex_key,)).fetchone()
                if row:
                    existing_id = row["id"]
                    duplicate_reason = "BibTeX key"
            if not existing_id and doi:
                row = conn.execute("SELECT id FROM papers WHERE doi = ?", (doi,)).fetchone()
                if row:
                    existing_id = row["id"]
                    duplicate_reason = "DOI"
            if not existing_id:
                title_norm = _normalize(title)
                if len(title_norm) >= 12:
                    rows = conn.execute("SELECT id, title FROM papers").fetchall()
                    for paper_row in rows:
                        if _normalize(paper_row["title"]) == title_norm:
                            existing_id = paper_row["id"]
                            duplicate_reason = "title"
                            break
            paper_id = existing_id or str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO papers (id, title, authors, year, bibtex_key, pdf_path, doi)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  title=excluded.title,
                  authors=excluded.authors,
                  year=excluded.year,
                  bibtex_key=excluded.bibtex_key,
                  pdf_path=excluded.pdf_path,
                  doi=excluded.doi,
                  updated_at=CURRENT_TIMESTAMP
                """,
                (paper_id, title, authors, year, bibtex_key, resolved_pdf_path, doi),
            )
            return UpsertPaperResult(paper_id=paper_id, duplicate_reason=duplicate_reason)

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
        fts_results = self._search_fts(query, limit, paper_ids)
        if fts_results:
            return fts_results

        return self._search_keywords(query, limit, paper_ids)

    def _search_fts(self, query: str, limit: int, paper_ids: list[str] | None = None) -> list[SearchResult]:
        match_query = _fts_query(query)
        if not match_query:
            return []
        params: list[object] = []
        paper_filter = ""
        if paper_ids:
            paper_filter = " AND p.id IN (%s)" % ",".join("?" for _ in paper_ids)
            params.extend(paper_ids)

        with self.database.connect() as conn:
            try:
                rows = conn.execute(
                    f"""
                    SELECT chunks_fts.chunk_id, p.id AS paper_id, p.title, p.authors, p.year, p.bibtex_key, c.text,
                           bm25(chunks_fts) AS rank
                    FROM chunks_fts
                    JOIN chunks c ON c.id = chunks_fts.chunk_id
                    JOIN papers p ON p.id = chunks_fts.paper_id
                    WHERE chunks_fts MATCH ? {paper_filter}
                    ORDER BY rank
                    LIMIT ?
                    """,
                    [match_query, *params, limit],
                ).fetchall()
            except Exception:
                return []

        return [
            SearchResult(
                paper_id=row["paper_id"],
                chunk_id=row["chunk_id"],
                title=row["title"],
                authors=row["authors"],
                year=row["year"],
                bibtex_key=row["bibtex_key"],
                snippet=snippet(row["text"], query),
                score=round(1 / (1 + max(float(row["rank"]), 0.0)), 4),
            )
            for row in rows
        ]

    def _search_keywords(self, query: str, limit: int = 10, paper_ids: list[str] | None = None) -> list[SearchResult]:
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

        ranked_candidates: list[CitationCandidate] = []
        for candidate in candidates:
            if paper_id and not (query or bibtex_key):
                score, reason = 100.0, "Selected paper"
            else:
                score, reason = citation_rank(query or bibtex_key, candidate)
            if query and not (paper_id or bibtex_key) and score <= 0:
                continue
            ranked_candidates.append(candidate.model_copy(update={"score": round(score, 4), "reason": reason}))

        ranked_candidates.sort(key=lambda item: (-(item.score or 0.0), item.bibtex_key))
        candidates = ranked_candidates
        return candidates[:limit]
