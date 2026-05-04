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


@dataclass(frozen=True)
class HotkeyResult:
    text: str
    copy_to_clipboard: bool = True


def _require_desktop_modules():
    try:
        import keyboard  # type: ignore
        import pyperclip  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Install desktop extras first: pip install -e .[desktop]") from exc
    return keyboard, pyperclip


def result_from_payload(data: dict[str, object]) -> HotkeyResult:
    if "result" in data:
        return HotkeyResult(str(data["result"]))
    if "answer" in data:
        return HotkeyResult(str(data["answer"]))
    if data.get("citation"):
        return HotkeyResult(str(data["citation"]))
    candidates = data.get("candidates") or []
    if candidates:
        lines = ["Multiple citation candidates:"]
        for item in candidates:
            lines.append(f"- {item.get('bibtex_key')}: {item.get('title') or 'Untitled'}")
        lines.append("Open the QuillPilot console to choose one; clipboard was left unchanged.")
        return HotkeyResult("\n".join(lines), copy_to_clipboard=False)
    return HotkeyResult(str(data.get("message") or data), copy_to_clipboard=False)


def call_api(config: HotkeyConfig, path: str, payload: dict[str, object]) -> HotkeyResult:
    try:
        with httpx.Client(timeout=60) as client:
            response = client.post(config.api_url.rstrip("/") + path, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        return HotkeyResult(f"QuillPilot request failed: {exc}", copy_to_clipboard=False)
    return result_from_payload(data)


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

    def run_clipboard_action(path: str, payload: dict[str, object]) -> None:
        text = read_clipboard()
        if not text:
            return
        if path == "/write/assist":
            request_payload = payload | {"text": text}
        elif path == "/read/ask":
            request_payload = payload | {"question": text}
        else:
            request_payload = payload | {"query": text}
        result = call_api(config, path, request_payload)
        if result.copy_to_clipboard:
            write_clipboard(result.text)
        else:
            print(result.text, file=sys.stderr)

    def explain() -> None:
        run_clipboard_action("/read/ask", {"top_k": 6})

    def write() -> None:
        run_clipboard_action("/write/assist", {"action": "polish", "top_k": 4})

    def cite() -> None:
        run_clipboard_action("/cite/insert", {"style": "cite", "top_k": 5})

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
