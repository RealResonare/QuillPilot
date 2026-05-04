from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Iterable

from .models import SearchResult


def snippet(text: str, query: str, size: int = 320) -> str:
    compact = " ".join(text.split())
    if len(compact) <= size:
        return compact
    lowered = compact.lower()
    idx = lowered.find(query.lower()) if query else -1
    if idx < 0:
        return compact[: size - 3] + "..."
    start = max(0, idx - size // 3)
    end = min(len(compact), start + size)
    prefix = "..." if start else ""
    suffix = "..." if end < len(compact) else ""
    return prefix + compact[start:end] + suffix


class OptionalChromaIndex:
    """Small ChromaDB adapter that silently disables itself when Chroma is absent."""

    def __init__(self, persist_dir: Path):
        self.enabled = False
        self.collection = None
        try:
            import chromadb  # type: ignore
            client = chromadb.PersistentClient(path=str(persist_dir))
            self.collection = client.get_or_create_collection("quillpilot_chunks")
        except Exception:
            return
        self.enabled = True

    def upsert_chunks(self, chunks: Iterable[dict[str, str]]) -> None:
        if not self.enabled or self.collection is None:
            return
        rows = list(chunks)
        if not rows:
            return
        try:
            self.collection.upsert(
                ids=[row["chunk_id"] for row in rows],
                documents=[row["text"] for row in rows],
                metadatas=[
                    {
                        "paper_id": row["paper_id"],
                        "title": row.get("title") or "",
                        "bibtex_key": row.get("bibtex_key") or "",
                    }
                    for row in rows
                ],
            )
        except Exception:
            return

    def query_chunks(self, query: str, limit: int = 10, paper_ids: list[str] | None = None) -> list[dict[str, object]]:
        if not self.enabled or self.collection is None or not query.strip():
            return []
        request: dict[str, object] = {
            "query_texts": [query],
            "n_results": limit,
            "include": ["metadatas", "distances"],
        }
        if paper_ids:
            request["where"] = {"paper_id": {"$in": paper_ids}}
        try:
            payload = self.collection.query(**request)
        except Exception:
            return []

        ids = (payload.get("ids") or [[]])[0]
        metadatas = (payload.get("metadatas") or [[]])[0]
        distances = (payload.get("distances") or [[]])[0]
        results: list[dict[str, object]] = []
        for index, chunk_id in enumerate(ids):
            metadata = metadatas[index] if index < len(metadatas) and metadatas[index] else {}
            distance = distances[index] if index < len(distances) else None
            results.append(
                {
                    "chunk_id": chunk_id,
                    "paper_id": metadata.get("paper_id"),
                    "distance": distance,
                }
            )
        return results


def keyword_score(query: str, *fields: str | None) -> float:
    terms = [term for term in query.lower().split() if term]
    if not terms:
        return 0.0
    haystack = " ".join(field or "" for field in fields).lower()
    if not haystack:
        return 0.0
    hits = sum(haystack.count(term) for term in terms)
    coverage = sum(1 for term in terms if term in haystack) / len(terms)
    return coverage + math.log1p(hits)


def stable_id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]
