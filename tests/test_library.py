from __future__ import annotations

from pathlib import Path

from reportlab.pdfgen import canvas

from quillpilot.bibtex import parse_bibtex_file
from quillpilot.chunking import chunk_text
from quillpilot.db import Database
from quillpilot.library import LibraryService, citation_command


def make_pdf(path: Path, text: str) -> None:
    c = canvas.Canvas(str(path))
    text_object = c.beginText(72, 760)
    for line in text.splitlines():
        text_object.textLine(line)
    c.drawText(text_object)
    c.save()


def test_parse_bibtex_file(tmp_path: Path) -> None:
    bib = tmp_path / "refs.bib"
    bib.write_text(
        """
@article{smith2024retrieval,
  title={Retrieval Augmented Academic Writing},
  author={Smith, Ada and Chen, Bo},
  year={2024},
  doi={10.1234/example}
}
""".strip(),
        encoding="utf-8",
    )

    entries = parse_bibtex_file(bib)

    assert len(entries) == 1
    assert entries[0].key == "smith2024retrieval"
    assert entries[0].title == "Retrieval Augmented Academic Writing"
    assert "smith2024retrieval" in entries[0].raw_bibtex


def test_chunk_text_has_overlap_safe_boundaries() -> None:
    chunks = chunk_text("Sentence one. " * 300, max_chars=500, overlap=50)

    assert len(chunks) > 1
    assert chunks[0].index == 0
    assert all(chunk.text for chunk in chunks)


def test_import_pdf_bib_search_and_citation(tmp_path: Path) -> None:
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    make_pdf(
        pdf_dir / "smith2024retrieval.pdf",
        "Retrieval augmented academic writing helps authors ground claims in sources.\n"
        "Citation insertion should use real BibTeX keys only.",
    )
    bib = tmp_path / "refs.bib"
    bib.write_text(
        """
@article{smith2024retrieval,
  title={Retrieval Augmented Academic Writing},
  author={Smith, Ada and Chen, Bo},
  year={2024}
}
""".strip(),
        encoding="utf-8",
    )
    service = LibraryService(Database(tmp_path / "quillpilot.sqlite3"))

    response = service.import_library(pdf_dir=str(pdf_dir), bib_file=str(bib))
    results = service.search("ground claims sources", limit=5)
    stats = service.stats()
    candidates = service.citation_candidates(query="retrieval academic writing")

    assert response.papers_imported == 1
    assert response.bib_entries_imported == 1
    assert response.chunks_indexed >= 1
    assert stats.papers_count == 1
    assert stats.bib_entries_count == 1
    assert stats.chunks_count >= 1
    assert results
    assert results[0].bibtex_key == "smith2024retrieval"
    assert candidates[0].bibtex_key == "smith2024retrieval"
    assert citation_command(candidates[0].bibtex_key, "citep") == "\\citep{smith2024retrieval}"


def test_import_deduplicates_papers_by_bibtex_key_doi_and_title(tmp_path: Path) -> None:
    service = LibraryService(Database(tmp_path / "quillpilot.sqlite3"))

    bib = tmp_path / "refs.bib"
    bib.write_text(
        """
@article{dup2024one,
  title={Duplicate Aware Citation Imports},
  author={Smith, Ada},
  year={2024},
  doi={10.1234/dup}
}

@article{dup2024two,
  title={Duplicate Aware Citation Imports Revised},
  author={Smith, Ada},
  year={2024},
  doi={10.1234/dup}
}
""".strip(),
        encoding="utf-8",
    )

    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    third_dir = tmp_path / "third"
    for directory in (first_dir, second_dir, third_dir):
        directory.mkdir()

    make_pdf(first_dir / "dup2024one.pdf", "First import text about duplicate aware citations.")
    make_pdf(second_dir / "dup2024one.pdf", "Second import text with the same BibTeX key.")
    make_pdf(third_dir / "dup2024two.pdf", "Third import text with the same DOI.")

    first = service.import_library(pdf_dir=str(first_dir), bib_file=str(bib))
    same_key = service.import_library(pdf_dir=str(second_dir), bib_file=str(bib))
    same_doi = service.import_library(pdf_dir=str(third_dir), bib_file=str(bib))
    stats = service.stats()

    assert first.papers_imported == 1
    assert same_key.papers_imported == 1
    assert same_doi.papers_imported == 1
    assert stats.papers_count == 1
    assert any("BibTeX key" in warning for warning in same_key.warnings)
    assert any("DOI" in warning for warning in same_doi.warnings)

    title_service = LibraryService(Database(tmp_path / "title.sqlite3"))
    title_first_dir = tmp_path / "title-first"
    title_second_dir = tmp_path / "title-second"
    title_first_dir.mkdir()
    title_second_dir.mkdir()
    make_pdf(title_first_dir / "same-title-paper.pdf", "First import text with title dedupe.")
    make_pdf(title_second_dir / "same-title-paper.pdf", "Second import text with title dedupe.")

    title_service.import_library(pdf_dir=str(title_first_dir))
    same_title = title_service.import_library(pdf_dir=str(title_second_dir))

    assert title_service.stats().papers_count == 1
    assert any("title" in warning for warning in same_title.warnings)
