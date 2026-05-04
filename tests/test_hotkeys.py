from __future__ import annotations

from quillpilot.hotkeys import result_from_payload


def test_hotkey_result_copies_generation_outputs() -> None:
    assert result_from_payload({"answer": "grounded answer"}).copy_to_clipboard is True
    assert result_from_payload({"result": "polished text"}).text == "polished text"
    assert result_from_payload({"citation": "\\cite{smith2024}"}).text == "\\cite{smith2024}"


def test_hotkey_result_keeps_clipboard_for_citation_candidates() -> None:
    result = result_from_payload(
        {
            "citation": None,
            "candidates": [
                {"bibtex_key": "smith2024", "title": "Retrieval Writing"},
                {"bibtex_key": "chen2025", "title": "Grounded Citation"},
            ],
        }
    )

    assert result.copy_to_clipboard is False
    assert "Multiple citation candidates" in result.text
    assert "smith2024" in result.text
    assert "clipboard was left unchanged" in result.text


def test_hotkey_result_keeps_clipboard_for_messages_without_output() -> None:
    result = result_from_payload({"message": "No reliable BibTeX key found."})

    assert result.copy_to_clipboard is False
    assert result.text == "No reliable BibTeX key found."
