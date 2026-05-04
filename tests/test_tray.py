from __future__ import annotations

from quillpilot import tray


class FakeProcess:
    def __init__(self) -> None:
        self.terminated = False
        self.killed = False
        self.returncode = None

    def poll(self):
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = 0

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9

    def wait(self, timeout=None):
        return self.returncode


def test_host_port_from_url_defaults() -> None:
    assert tray._host_port_from_url("http://127.0.0.1:8765") == ("127.0.0.1", 8765)
    assert tray._host_port_from_url("http://localhost") == ("localhost", 8765)


def test_controller_starts_api_with_configured_url(monkeypatch) -> None:
    spawned: list[list[str]] = []

    def fake_spawn(command: list[str]) -> FakeProcess:
        spawned.append(command)
        return FakeProcess()

    controller = tray.TrayController("http://127.0.0.1:9999")
    monkeypatch.setattr(controller, "api_ready", lambda: False)
    monkeypatch.setattr(tray, "_spawn", fake_spawn)

    controller.start_api()

    assert spawned
    command = spawned[0]
    assert command[:3] == [tray.sys.executable, "-m", "uvicorn"]
    assert command[-4:] == ["--host", "127.0.0.1", "--port", "9999"]


def test_controller_starts_hotkeys_after_api(monkeypatch) -> None:
    spawned: list[list[str]] = []

    def fake_spawn(command: list[str]) -> FakeProcess:
        spawned.append(command)
        return FakeProcess()

    controller = tray.TrayController("http://127.0.0.1:8765")
    monkeypatch.setattr(controller, "api_ready", lambda: False)
    monkeypatch.setattr(tray, "_spawn", fake_spawn)

    controller.start_hotkeys()

    assert len(spawned) == 2
    assert spawned[0][:3] == [tray.sys.executable, "-m", "uvicorn"]
    assert spawned[1] == [tray.sys.executable, "-m", "quillpilot.hotkeys", "--api-url", "http://127.0.0.1:8765"]


def test_controller_stop_all_terminates_managed_processes(monkeypatch) -> None:
    controller = tray.TrayController()
    monkeypatch.setattr(controller, "api_ready", lambda: False)
    controller.api_process = FakeProcess()
    controller.hotkeys_process = FakeProcess()

    controller.stop_all()

    assert controller.api_process is None
    assert controller.hotkeys_process is None
