from __future__ import annotations


def main() -> int:
    """Placeholder for a Windows tray launcher.

    The MVP exposes the local API and hotkey client first. A tray UI can wrap
    these commands without changing the service contract.
    """

    print("Tray launcher is reserved for the next desktop packaging pass.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
