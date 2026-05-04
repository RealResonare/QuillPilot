from __future__ import annotations

import json
from uuid import uuid4

from pydantic import ValidationError

from .config import Settings
from .db import Database
from .llm import LLMConfig
from .models import APIProviderSettings, AppSettings, GeneralSettings, HotkeySettings


def default_app_settings(config: Settings) -> AppSettings:
    env_provider_id = "openai-compatible"
    providers = [
        APIProviderSettings(
            id=env_provider_id,
            name="OpenAI Compatible",
            kind="api",
            base_url=config.llm_base_url,
            model=config.llm_model,
            api_key=config.llm_api_key or "",
            enabled=True,
        ),
        APIProviderSettings(
            id="local-llm",
            name="Local LLM",
            kind="local",
            base_url="http://127.0.0.1:11434/v1",
            model="llama3.1",
            api_key="",
            enabled=False,
        ),
    ]
    return AppSettings(
        general=GeneralSettings(),
        providers=providers,
        default_provider_id=env_provider_id,
        hotkeys=HotkeySettings(),
    )


class SettingsService:
    def __init__(self, database: Database, config: Settings):
        self.database = database
        self.config = config

    def get(self) -> AppSettings:
        with self.database.connect() as conn:
            row = conn.execute("SELECT general_json, providers_json, hotkeys_json FROM app_settings WHERE id = 1").fetchone()
        if not row:
            value = default_app_settings(self.config)
            self.save(value)
            return value

        try:
            general = GeneralSettings.model_validate(json.loads(row["general_json"]))
            providers_payload = json.loads(row["providers_json"])
            hotkeys = HotkeySettings.model_validate(json.loads(row["hotkeys_json"]))
            providers = [APIProviderSettings.model_validate(item) for item in providers_payload.get("providers", [])]
            return AppSettings(
                general=general,
                providers=providers,
                default_provider_id=providers_payload.get("default_provider_id"),
                hotkeys=hotkeys,
            )
        except (json.JSONDecodeError, ValidationError):
            value = default_app_settings(self.config)
            self.save(value)
            return value

    def save(self, value: AppSettings) -> AppSettings:
        normalized = self._normalize(value)
        providers_payload = {
            "providers": [provider.model_dump() for provider in normalized.providers],
            "default_provider_id": normalized.default_provider_id,
        }
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO app_settings (id, general_json, providers_json, hotkeys_json)
                VALUES (1, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  general_json=excluded.general_json,
                  providers_json=excluded.providers_json,
                  hotkeys_json=excluded.hotkeys_json,
                  updated_at=CURRENT_TIMESTAMP
                """,
                (
                    normalized.general.model_dump_json(),
                    json.dumps(providers_payload),
                    normalized.hotkeys.model_dump_json(),
                ),
            )
        return normalized

    def llm_config(self) -> LLMConfig:
        value = self.get()
        provider = next(
            (
                item
                for item in value.providers
                if item.id == value.default_provider_id and item.enabled
            ),
            None,
        )
        if provider:
            return LLMConfig(
                api_key=provider.api_key or None,
                base_url=provider.base_url,
                model=provider.model,
                requires_api_key=provider.kind == "api",
                timeout_seconds=self.config.llm_timeout_seconds,
            )
        return LLMConfig(
            api_key=self.config.llm_api_key,
            base_url=self.config.llm_base_url,
            model=self.config.llm_model,
            requires_api_key=True,
            timeout_seconds=self.config.llm_timeout_seconds,
        )

    @staticmethod
    def _normalize(value: AppSettings) -> AppSettings:
        providers = []
        seen_ids: set[str] = set()
        for provider in value.providers:
            provider_id = provider.id.strip() or f"provider-{uuid4().hex[:8]}"
            while provider_id in seen_ids:
                provider_id = f"provider-{uuid4().hex[:8]}"
            seen_ids.add(provider_id)
            providers.append(provider.model_copy(update={"id": provider_id}))

        default_id = value.default_provider_id
        if default_id not in seen_ids:
            enabled = next((item.id for item in providers if item.enabled), None)
            default_id = enabled or (providers[0].id if providers else None)

        return AppSettings(
            general=value.general,
            providers=providers,
            default_provider_id=default_id,
            hotkeys=value.hotkeys,
        )
