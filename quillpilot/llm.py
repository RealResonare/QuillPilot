from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from .models import SourceSnippet, WriteAction


@dataclass(frozen=True)
class LLMConfig:
    api_key: str | None
    base_url: str
    model: str
    requires_api_key: bool = True
    timeout_seconds: float = 45


class LLMProvider:
    def __init__(self, config: LLMConfig):
        self.config = config

    def complete(self, system: str, user: str) -> str:
        if self.config.requires_api_key and not self.config.api_key:
            return self._offline_response(user)

        endpoint = self.config.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        try:
            with httpx.Client(timeout=self.config.timeout_seconds) as client:
                response = client.post(endpoint, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc

        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected LLM response shape: {json.dumps(data)[:500]}") from exc

    @staticmethod
    def _offline_response(user: str) -> str:
        return (
            "No QUILLPILOT_API_KEY or OPENAI_API_KEY is configured. "
            "QuillPilot prepared the request locally, but AI generation requires an OpenAI-compatible API key.\n\n"
            f"Request preview:\n{user[:1200]}"
        )


def sources_to_context(sources: list[SourceSnippet]) -> str:
    if not sources:
        return "No retrieved source snippets."
    blocks = []
    for idx, source in enumerate(sources, 1):
        key = f" ({source.bibtex_key})" if source.bibtex_key else ""
        blocks.append(f"[{idx}] {source.title}{key}\n{source.snippet}")
    return "\n\n".join(blocks)


def ask_prompt(question: str, sources: list[SourceSnippet]) -> tuple[str, str]:
    system = (
        "You are QuillPilot, an academic writing copilot. Answer using only the provided personal-library "
        "source snippets. If the snippets are insufficient, say what is missing. Keep citations tied to source numbers."
    )
    user = f"Question:\n{question}\n\nSources:\n{sources_to_context(sources)}"
    return system, user


def write_prompt(text: str, action: WriteAction, context: str | None, sources: list[SourceSnippet]) -> tuple[str, str]:
    action_instruction = {
        "polish": "Polish the text into clear academic prose without changing the claim.",
        "expand": "Expand the text into a more complete academic paragraph.",
        "rewrite": "Rewrite the text for clarity, precision, and flow.",
        "summarize": "Summarize the text concisely for research notes.",
        "outline": "Turn the text into a structured paper-section outline.",
        "counterargument": "Suggest rigorous counterarguments or limitations.",
    }[action]
    system = (
        "You are QuillPilot, an academic writing copilot for research authors. Preserve technical meaning, "
        "avoid fabricated citations, and only mention sources when supported by retrieved snippets."
    )
    user = (
        f"Task:\n{action_instruction}\n\n"
        f"Selected text:\n{text}\n\n"
        f"User context:\n{context or 'None'}\n\n"
        f"Personal-library snippets:\n{sources_to_context(sources)}"
    )
    return system, user
