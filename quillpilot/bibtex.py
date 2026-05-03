from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase


@dataclass(frozen=True)
class BibEntry:
    key: str
    entry_type: str
    title: str | None
    authors: str | None
    year: str | None
    doi: str | None
    raw_bibtex: str


def _entry_to_raw(entry: dict[str, str]) -> str:
    db = BibDatabase()
    db.entries = [entry]
    writer = BibTexWriter()
    writer.indent = "  "
    return writer.write(db).strip()


def parse_bibtex_file(path: Path | str) -> list[BibEntry]:
    bib_path = Path(path)
    with bib_path.open("r", encoding="utf-8") as handle:
        database = bibtexparser.load(handle)

    entries: list[BibEntry] = []
    for entry in database.entries:
        key = entry.get("ID")
        if not key:
            continue
        entries.append(
            BibEntry(
                key=key,
                entry_type=entry.get("ENTRYTYPE", "article"),
                title=entry.get("title"),
                authors=entry.get("author"),
                year=entry.get("year"),
                doi=entry.get("doi"),
                raw_bibtex=_entry_to_raw(entry),
            )
        )
    return entries
