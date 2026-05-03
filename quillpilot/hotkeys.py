from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

import httpx


DEFAULT_API_URL = "http://127.0.0.1:8765"


@dataclass(frozen=True)
class HotkeyConfig:
    api_url: str = DEFAULT_API_URL
    enabled: bool = True
    read: str = "ctrl+alt+r"
    write: str = "ctrl+alt+w"
    cite: str = "ctrl+alt+c"


def _require_desktop_modules():
    try:
        import keyboard  # type: ignore
        import pyperclip  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Install desktop extras first: pip install -e .[desktop]") from exc
    return keyboard, pyperclip


def call_api(config: HotkeyConfig, path: str, payload: dict[str, object]) -> str:
    with httpx.Client(timeout=60) as client:
        response = client.post(config.api_url.rstrip("/") + path, json=payload)
        response.raise_for_status()
        data = response.json()
    if "result" in data:
        return str(data["result"])
    if "answer" in data:
        return str(data["answer"])
    if data.get("citation"):
        return str(data["citation"])
    candidates = data.get("candidates") or []
    if candidates:
        lines = ["Multiple citation candidates:"]
        for item in candidates:
            lines.append(f"- {item.get('bibtex_key')}: {item.get('title') or 'Untitled'}")
        return "\n".join(lines)
    return str(data.get("message") or data)


def load_hotkey_config(api_url: str) -> HotkeyConfig:
    try:
        with httpx.Client(timeout=5) as client:
            response = client.get(api_url.rstrip("/") + "/settings")
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError:
        return HotkeyConfig(api_url=api_url)

    hotkeys = payload.get("hotkeys") or {}
    return HotkeyConfig(
        api_url=api_url,
        enabled=bool(hotkeys.get("enabled", True)),
        read=str(hotkeys.get("read") or "ctrl+alt+r"),
        write=str(hotkeys.get("write") or "ctrl+alt+w"),
        cite=str(hotkeys.get("cite") or "ctrl+alt+c"),
    )


def install_hotkeys(config: HotkeyConfig) -> None:
    keyboard, pyperclip = _require_desktop_modules()
    if not config.enabled:
        print("QuillPilot hotkeys are disabled in settings.")
        return

    def read_clipboard() -> str:
        text = pyperclip.paste()
        return text.strip() if isinstance(text, str) else ""

    def write_clipboard(text: str) -> None:
        pyperclip.copy(text)

    def explain() -> None:
        text = read_clipboard()
        if text:
            write_clipboard(call_api(config, "/read/ask", {"question": text, "top_k": 6}))

    def write() -> None:
        text = read_clipboard()
        if text:
            write_clipboard(call_api(config, "/write/assist", {"text": text, "action": "polish", "top_k": 4}))

    def cite() -> None:
        text = read_clipboard()
        if text:
            write_clipboard(call_api(config, "/cite/insert", {"query": text, "style": "cite", "top_k": 5}))

    keyboard.add_hotkey(config.read, explain)
    keyboard.add_hotkey(config.write, write)
    keyboard.add_hotkey(config.cite, cite)
    print(f"QuillPilot hotkeys active: {config.read} read, {config.write} write, {config.cite} cite")
    keyboard.wait()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="QuillPilot global hotkey client.")
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    args = parser.parse_args(argv)
    try:
        install_hotkeys(load_hotkey_config(args.api_url))
    except Exception as exc:
        print(f"Hotkey client failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
