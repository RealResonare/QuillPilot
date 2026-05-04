from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ImportRequest(BaseModel):
    pdf_dir: str | None = Field(default=None, description="Directory containing PDFs to import.")
    bib_file: str | None = Field(default=None, description="BibTeX file to import.")


class ImportResponse(BaseModel):
    papers_imported: int
    bib_entries_imported: int
    chunks_indexed: int
    warnings: list[str] = Field(default_factory=list)


TaskStatus = Literal["queued", "running", "completed", "failed"]


class ImportTaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    detail: str | None = None
    result: ImportResponse | None = None
    warnings: list[str] = Field(default_factory=list)


class LibraryStats(BaseModel):
    papers_count: int
    bib_entries_count: int
    chunks_count: int
    latest_import_at: str | None = None
    latest_task_status: TaskStatus | None = None


class SearchResult(BaseModel):
    paper_id: str
    chunk_id: str | None = None
    title: str
    authors: str | None = None
    year: str | None = None
    bibtex_key: str | None = None
    snippet: str
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


class ReadAskRequest(BaseModel):
    question: str
    paper_ids: list[str] | None = None
    top_k: int = Field(default=6, ge=1, le=20)


class SourceSnippet(BaseModel):
    paper_id: str
    chunk_id: str
    title: str
    bibtex_key: str | None = None
    snippet: str


class ReadAskResponse(BaseModel):
    answer: str
    sources: list[SourceSnippet]


WriteAction = Literal["polish", "expand", "rewrite", "summarize", "outline", "counterargument"]


class WriteAssistRequest(BaseModel):
    text: str
    action: WriteAction = "polish"
    context: str | None = None
    top_k: int = Field(default=4, ge=0, le=12)


class WriteAssistResponse(BaseModel):
    action: WriteAction
    result: str
    sources: list[SourceSnippet] = Field(default_factory=list)


CitationStyle = Literal["cite", "citep", "citet"]


class CitationRequest(BaseModel):
    query: str | None = None
    paper_id: str | None = None
    bibtex_key: str | None = None
    style: CitationStyle = "cite"
    top_k: int = Field(default=5, ge=1, le=10)


class CitationCandidate(BaseModel):
    paper_id: str | None = None
    bibtex_key: str
    title: str | None = None
    authors: str | None = None
    year: str | None = None


class CitationResponse(BaseModel):
    citation: str | None
    candidates: list[CitationCandidate] = Field(default_factory=list)
    message: str


Language = Literal["zh-CN", "en-US", "fr-FR"]
ProviderKind = Literal["api", "local"]


class GeneralSettings(BaseModel):
    language: Language = "zh-CN"
    font_family: str = "Nunito Sans"
    code_font_family: str = "Source Code Pro"
    font_size: int = Field(default=14, ge=11, le=20)
    compact_mode: bool = True
    show_progress: bool = True


class APIProviderSettings(BaseModel):
    id: str
    name: str
    kind: ProviderKind = "api"
    base_url: str
    model: str
    api_key: str = ""
    enabled: bool = True


class HotkeySettings(BaseModel):
    enabled: bool = True
    read: str = "ctrl+alt+r"
    write: str = "ctrl+alt+w"
    cite: str = "ctrl+alt+c"


class AppSettings(BaseModel):
    general: GeneralSettings = Field(default_factory=GeneralSettings)
    providers: list[APIProviderSettings] = Field(default_factory=list)
    default_provider_id: str | None = None
    hotkeys: HotkeySettings = Field(default_factory=HotkeySettings)
