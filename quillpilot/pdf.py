from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass(frozen=True)
class ExtractedPdf:
    path: Path
    text: str
    page_count: int
    title_hint: str


def extract_pdf_text(path: Path | str) -> ExtractedPdf:
    pdf_path = Path(path)
    parts: list[str] = []
    with fitz.open(pdf_path) as document:
        metadata_title = (document.metadata or {}).get("title") or ""
        for page in document:
            parts.append(page.get_text("text"))
        title_hint = metadata_title.strip() or pdf_path.stem.replace("_", " ").replace("-", " ")
        return ExtractedPdf(
            path=pdf_path,
            text="\n".join(parts).strip(),
            page_count=document.page_count,
            title_hint=title_hint,
        )
