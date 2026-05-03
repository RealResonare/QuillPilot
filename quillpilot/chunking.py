from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    index: int
    text: str
    page_start: int | None = None
    page_end: int | None = None


def chunk_text(text: str, max_chars: int = 1800, overlap: int = 220) -> list[TextChunk]:
    normalized = " ".join(text.split())
    if not normalized:
        return []
    if max_chars <= overlap:
        raise ValueError("max_chars must be greater than overlap")

    chunks: list[TextChunk] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + max_chars)
        if end < len(normalized):
            boundary = max(normalized.rfind(". ", start, end), normalized.rfind("; ", start, end))
            if boundary > start + max_chars // 2:
                end = boundary + 1
        chunks.append(TextChunk(index=len(chunks), text=normalized[start:end].strip()))
        if end >= len(normalized):
            break
        start = max(0, end - overlap)
    return chunks
