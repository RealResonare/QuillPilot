from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from quillpilot import api


def make_pdf(path: Path, text: str) -> None:
    c = canvas.Canvas(str(path))
    text_object = c.beginText(72, 760)
    for line in text.splitlines():
        text_object.textLine(line)
    c.drawText(text_object)
    c.save()


def clear_api_caches() -> None:
    api.settings.cache_clear()
    api.library_service.cache_clear()
    api.settings_service.cache_clear()
    api.llm_provider.cache_clear()


def test_api_import_search_read_write_and_cite(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("QUILLPILOT_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("QUILLPILOT_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    clear_api_caches()

    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    make_pdf(
        pdf_dir / "doe2025copilot.pdf",
        "Academic copilots can help authors connect literature review and writing workflows.",
    )
    bib = tmp_path / "refs.bib"
    bib.write_text(
        """
@inproceedings{doe2025copilot,
  title={Academic Copilots for Literature Review},
  author={Doe, Jane},
  year={2025}
}
""".strip(),
        encoding="utf-8",
    )

    client = TestClient(api.create_app())

    imported = client.post("/library/import", json={"pdf_dir": str(pdf_dir), "bib_file": str(bib)})
    assert imported.status_code == 200
    assert imported.json()["papers_imported"] == 1

    stats = client.get("/library/stats")
    assert stats.status_code == 200
    assert stats.json()["papers_count"] == 1
    assert stats.json()["bib_entries_count"] == 1
    assert stats.json()["chunks_count"] >= 1

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["library"]["papers_count"] == 1

    searched = client.get("/library/search", params={"q": "literature review writing"})
    assert searched.status_code == 200
    assert searched.json()["results"][0]["bibtex_key"] == "doe2025copilot"

    asked = client.post("/read/ask", json={"question": "How do copilots help authors?", "top_k": 3})
    assert asked.status_code == 200
    assert "API_KEY" in asked.json()["answer"]
    assert asked.json()["sources"]

    written = client.post("/write/assist", json={"text": "This method is good.", "action": "polish", "top_k": 0})
    assert written.status_code == 200
    assert written.json()["action"] == "polish"

    cited = client.post("/cite/insert", json={"query": "Academic Copilots", "style": "cite"})
    assert cited.status_code == 200
    assert cited.json()["citation"] == "\\cite{doe2025copilot}"


def test_import_task_records_result(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("QUILLPILOT_DATA_DIR", str(tmp_path / "data"))
    clear_api_caches()

    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    make_pdf(pdf_dir / "task2026.pdf", "Task based import should record indexed chunks.")

    client = TestClient(api.create_app())

    created = client.post("/library/import/tasks", json={"pdf_dir": str(pdf_dir)})
    assert created.status_code == 200
    task_id = created.json()["task_id"]

    fetched = client.get(f"/library/import/tasks/{task_id}")
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "completed"
    assert fetched.json()["result"]["papers_imported"] == 1


def test_citation_candidates_require_explicit_choice(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("QUILLPILOT_DATA_DIR", str(tmp_path / "data"))
    clear_api_caches()

    bib = tmp_path / "refs.bib"
    bib.write_text(
        """
@article{smith2024retrieval,
  title={Retrieval Augmented Academic Writing},
  author={Smith, Ada},
  year={2024}
}

@article{chen2025retrieval,
  title={Retrieval Grounded Citation Tools},
  author={Chen, Bo},
  year={2025}
}
""".strip(),
        encoding="utf-8",
    )
    client = TestClient(api.create_app())

    imported = client.post("/library/import", json={"bib_file": str(bib)})
    assert imported.status_code == 200
    assert imported.json()["bib_entries_imported"] == 2

    candidates = client.post("/cite/insert", json={"query": "retrieval", "style": "citep"})
    assert candidates.status_code == 200
    assert candidates.json()["citation"] is None
    assert len(candidates.json()["candidates"]) == 2

    selected = client.post("/cite/insert", json={"bibtex_key": "chen2025retrieval", "style": "citep"})
    assert selected.status_code == 200
    assert selected.json()["citation"] == "\\citep{chen2025retrieval}"


def test_settings_round_trip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("QUILLPILOT_DATA_DIR", str(tmp_path / "data"))
    clear_api_caches()

    client = TestClient(api.create_app())

    current = client.get("/settings")
    assert current.status_code == 200
    payload = current.json()
    payload["general"]["language"] = "en-US"
    payload["general"]["font_size"] = 16
    payload["providers"].append(
        {
            "id": "test-local",
            "name": "Test Local",
            "kind": "local",
            "base_url": "http://127.0.0.1:11434/v1",
            "model": "llama3.1",
            "api_key": "",
            "enabled": True,
        }
    )
    payload["default_provider_id"] = "test-local"
    payload["hotkeys"]["read"] = "ctrl+shift+r"

    saved = client.put("/settings", json=payload)
    health = client.get("/health")

    assert saved.status_code == 200
    assert saved.json()["general"]["language"] == "en-US"
    assert saved.json()["hotkeys"]["read"] == "ctrl+shift+r"
    assert health.json()["llm_configured"] is True
    assert health.json()["default_provider"] == "Test Local"


def test_ui_is_served(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("QUILLPILOT_DATA_DIR", str(tmp_path / "data"))
    clear_api_caches()

    client = TestClient(api.create_app())

    root = client.get("/")
    css = client.get("/static/styles.css")
    js = client.get("/static/app.js")

    assert root.status_code == 200
    assert "Research Writing Console" in root.text
    assert 'href="#home"' in root.text
    assert 'href="#repository"' in root.text
    assert 'data-i18n="providers.title"' in root.text
    assert css.status_code == 200
    assert ".app-view.active" in css.text
    assert "--primary: #00a1e0" in css.text
    assert ".citation-candidate" in css.text
    assert js.status_code == 200
    assert "const I18N" in js.text
    assert "syncRouteFromHash" in js.text
    assert "renderCitationCandidates" in js.text
    assert "citation-candidate" in js.text
    assert "data-bibtex-key" in js.text
