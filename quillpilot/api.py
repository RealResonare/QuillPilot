from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import Settings
from .db import Database
from .library import LibraryService, citation_command
from .llm import LLMProvider, ask_prompt, write_prompt
from .models import (
    AppSettings,
    CitationRequest,
    CitationResponse,
    ImportRequest,
    ImportResponse,
    ImportTaskResponse,
    LibraryStats,
    ReadAskRequest,
    ReadAskResponse,
    SearchResponse,
    SourceSnippet,
    WriteAssistRequest,
    WriteAssistResponse,
)
from .search import OptionalChromaIndex
from .user_settings import SettingsService


@lru_cache
def settings() -> Settings:
    value = Settings.from_env()
    value.ensure_dirs()
    return value


@lru_cache
def library_service() -> LibraryService:
    config = settings()
    vector_index = OptionalChromaIndex(config.vector_dir)
    return LibraryService(Database(config.database_path), vector_index)


@lru_cache
def settings_service() -> SettingsService:
    config = settings()
    return SettingsService(Database(config.database_path), config)


@lru_cache
def llm_provider() -> LLMProvider:
    return LLMProvider(settings_service().llm_config())


def create_app() -> FastAPI:
    app = FastAPI(
        title="QuillPilot Local API",
        version="0.2.0",
        description="Editor-agnostic local AI copilot for academic writing.",
    )
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

        @app.get("/", include_in_schema=False)
        def ui() -> FileResponse:
            return FileResponse(static_dir / "index.html")

    @app.get("/health")
    def health() -> dict[str, object]:
        config = settings()
        app_settings = settings_service().get()
        stats = library_service().stats()
        default_provider = next(
            (item for item in app_settings.providers if item.id == app_settings.default_provider_id),
            None,
        )
        llm_ready = bool(default_provider and default_provider.enabled and (default_provider.kind == "local" or default_provider.api_key))
        return {
            "ok": True,
            "database": str(config.database_path),
            "llm_configured": llm_ready,
            "default_provider": default_provider.name if default_provider else None,
            "library": stats.model_dump(),
        }

    @app.get("/settings", response_model=AppSettings)
    def get_settings() -> AppSettings:
        return settings_service().get()

    @app.put("/settings", response_model=AppSettings)
    def put_settings(request: AppSettings) -> AppSettings:
        saved = settings_service().save(request)
        llm_provider.cache_clear()
        return saved

    @app.post("/library/import", response_model=ImportResponse)
    def import_library(request: ImportRequest) -> ImportResponse:
        if not request.pdf_dir and not request.bib_file:
            raise HTTPException(status_code=400, detail="Provide pdf_dir, bib_file, or both.")
        try:
            return library_service().import_library(pdf_dir=request.pdf_dir, bib_file=request.bib_file)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/library/import/tasks", response_model=ImportTaskResponse)
    def create_import_task(request: ImportRequest, background_tasks: BackgroundTasks) -> ImportTaskResponse:
        if not request.pdf_dir and not request.bib_file:
            raise HTTPException(status_code=400, detail="Provide pdf_dir, bib_file, or both.")
        task = library_service().create_import_task(request)
        background_tasks.add_task(library_service().run_import_task, task.task_id, request)
        return task

    @app.get("/library/import/tasks/{task_id}", response_model=ImportTaskResponse)
    def get_import_task(task_id: str) -> ImportTaskResponse:
        try:
            return library_service().get_task(task_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Import task not found: {task_id}") from exc

    @app.get("/library/stats", response_model=LibraryStats)
    def library_stats() -> LibraryStats:
        return library_service().stats()

    @app.get("/library/search", response_model=SearchResponse)
    def search_library(q: str = Query(..., min_length=1), limit: int = Query(default=10, ge=1, le=50)) -> SearchResponse:
        return SearchResponse(query=q, results=library_service().search(q, limit=limit))

    @app.post("/read/ask", response_model=ReadAskResponse)
    def read_ask(request: ReadAskRequest) -> ReadAskResponse:
        results = library_service().search(request.question, limit=request.top_k, paper_ids=request.paper_ids)
        sources = [
            SourceSnippet(
                paper_id=result.paper_id,
                chunk_id=result.chunk_id or "",
                title=result.title,
                bibtex_key=result.bibtex_key,
                snippet=result.snippet,
            )
            for result in results
            if result.chunk_id
        ]
        system, user = ask_prompt(request.question, sources)
        answer = llm_provider().complete(system, user)
        return ReadAskResponse(answer=answer, sources=sources)

    @app.post("/write/assist", response_model=WriteAssistResponse)
    def write_assist(request: WriteAssistRequest) -> WriteAssistResponse:
        sources: list[SourceSnippet] = []
        if request.top_k > 0:
            query = request.context or request.text
            results = library_service().search(query, limit=request.top_k)
            sources = [
                SourceSnippet(
                    paper_id=result.paper_id,
                    chunk_id=result.chunk_id or "",
                    title=result.title,
                    bibtex_key=result.bibtex_key,
                    snippet=result.snippet,
                )
                for result in results
                if result.chunk_id
            ]
        system, user = write_prompt(request.text, request.action, request.context, sources)
        result = llm_provider().complete(system, user)
        return WriteAssistResponse(action=request.action, result=result, sources=sources)

    @app.post("/cite/insert", response_model=CitationResponse)
    def cite_insert(request: CitationRequest) -> CitationResponse:
        if not (request.query or request.paper_id or request.bibtex_key):
            raise HTTPException(status_code=400, detail="Provide query, paper_id, or bibtex_key.")
        candidates = library_service().citation_candidates(
            query=request.query,
            paper_id=request.paper_id,
            bibtex_key=request.bibtex_key,
            limit=request.top_k,
        )
        if len(candidates) == 1:
            return CitationResponse(
                citation=citation_command(candidates[0].bibtex_key, request.style),
                candidates=candidates,
                message="Exact citation match found.",
            )
        if not candidates:
            return CitationResponse(
                citation=None,
                candidates=[],
                message="No reliable BibTeX key found in the imported library.",
            )
        return CitationResponse(
            citation=None,
            candidates=candidates,
            message="Multiple citation candidates found; choose one explicitly by bibtex_key or paper_id.",
        )

    return app


app = create_app()


def run() -> None:
    uvicorn.run("quillpilot.api:app", host="127.0.0.1", port=8765, reload=False)


if __name__ == "__main__":
    run()
