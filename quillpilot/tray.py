from __future__ import annotations

import argparse
import os
import subprocess
import sys
import webbrowser
from dataclasses import dataclass

import httpx


DEFAULT_API_URL = "http://127.0.0.1:8765"


def _require_tray_modules():
    try:
        import pystray  # type: ignore
        from PIL import Image, ImageDraw, ImageFont  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Install desktop extras first: pip install -e .[desktop]") from exc
    return pystray, Image, ImageDraw, ImageFont


def _hidden_startupinfo() -> subprocess.STARTUPINFO | None:
    if os.name != "nt":
        return None
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0
    return startupinfo


def _spawn(command: list[str]) -> subprocess.Popen:
    return subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=_hidden_startupinfo(),
    )


@dataclass(frozen=True)
class TrayStatus:
    api_running: bool
    hotkeys_running: bool
    api_ready: bool

    @property
    def label(self) -> str:
        if self.api_ready and self.hotkeys_running:
            return "API ready, hotkeys active"
        if self.api_ready:
            return "API ready"
        if self.api_running:
            return "API starting"
        return "Stopped"


class TrayController:
    def __init__(self, api_url: str = DEFAULT_API_URL):
        self.api_url = api_url.rstrip("/")
        self.api_process: subprocess.Popen | None = None
        self.hotkeys_process: subprocess.Popen | None = None

    @staticmethod
    def _running(process: subprocess.Popen | None) -> bool:
        return bool(process and process.poll() is None)

    def status(self) -> TrayStatus:
        return TrayStatus(
            api_running=self._running(self.api_process),
            hotkeys_running=self._running(self.hotkeys_process),
            api_ready=self.api_ready(),
        )

    def api_ready(self) -> bool:
        try:
            response = httpx.get(f"{self.api_url}/health", timeout=1.5)
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    def start_api(self) -> None:
        if self.api_ready() or self._running(self.api_process):
            return
        host, port = _host_port_from_url(self.api_url)
        self.api_process = _spawn(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "quillpilot.api:app",
                "--host",
                host,
                "--port",
                str(port),
            ]
        )

    def stop_api(self) -> None:
        self._stop_process("api_process")

    def start_hotkeys(self) -> None:
        if self._running(self.hotkeys_process):
            return
        self.start_api()
        self.hotkeys_process = _spawn([sys.executable, "-m", "quillpilot.hotkeys", "--api-url", self.api_url])

    def stop_hotkeys(self) -> None:
        self._stop_process("hotkeys_process")

    def open_console(self) -> None:
        self.start_api()
        webbrowser.open(self.api_url)

    def stop_all(self) -> None:
        self.stop_hotkeys()
        self.stop_api()

    def _stop_process(self, attr: str) -> None:
        process = getattr(self, attr)
        if not self._running(process):
            setattr(self, attr, None)
            return
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        setattr(self, attr, None)


def _host_port_from_url(api_url: str) -> tuple[str, int]:
    from urllib.parse import urlparse

    parsed = urlparse(api_url)
    return parsed.hostname or "127.0.0.1", parsed.port or 8765


def create_icon_image():
    _, Image, ImageDraw, ImageFont = _require_tray_modules()
    image = Image.new("RGBA", (64, 64), "#032D60")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, 56, 56), radius=12, fill="#00A1E0")
    try:
        font = ImageFont.truetype("arial.ttf", 34)
    except Exception:
        font = ImageFont.load_default()
    draw.text((21, 14), "Q", fill="white", font=font)
    draw.line((40, 42, 50, 52), fill="white", width=4)
    return image


def run_tray(api_url: str = DEFAULT_API_URL) -> None:
    pystray, _, _, _ = _require_tray_modules()
    controller = TrayController(api_url)
    controller.start_api()

    def refresh(icon) -> None:
        icon.title = f"QuillPilot - {controller.status().label}"
        icon.update_menu()

    def open_console(icon, _item) -> None:
        controller.open_console()
        refresh(icon)

    def start_api(icon, _item) -> None:
        controller.start_api()
        refresh(icon)

    def stop_api(icon, _item) -> None:
        controller.stop_api()
        refresh(icon)

    def start_hotkeys(icon, _item) -> None:
        controller.start_hotkeys()
        refresh(icon)

    def stop_hotkeys(icon, _item) -> None:
        controller.stop_hotkeys()
        refresh(icon)

    def quit_app(icon, _item) -> None:
        controller.stop_all()
        icon.stop()

    def status_text(_item) -> str:
        return controller.status().label

    menu = pystray.Menu(
        pystray.MenuItem(status_text, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Open Console", open_console, default=True),
        pystray.MenuItem("Start API", start_api),
        pystray.MenuItem("Stop API", stop_api),
        pystray.MenuItem("Start Hotkeys", start_hotkeys),
        pystray.MenuItem("Stop Hotkeys", stop_hotkeys),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", quit_app),
    )
    icon = pystray.Icon("quillpilot", create_icon_image(), "QuillPilot", menu)
    icon.run()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="QuillPilot Windows tray launcher.")
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    args = parser.parse_args(argv)
    try:
        run_tray(args.api_url)
    except Exception as exc:
        print(f"Tray launcher failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
