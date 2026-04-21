from __future__ import annotations

import ctypes
import subprocess
import sys
from pathlib import Path

from dnf_tool.ui.main_window import DnfAutomationApp


def _ensure_admin_privileges() -> None:
    if sys.platform != "win32":
        return

    try:
        is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
    except OSError:
        is_admin = False

    if is_admin:
        return

    executable, parameters = _build_elevation_command()
    result = ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        executable,
        parameters,
        None,
        1,
    )
    if result <= 32:
        ctypes.windll.user32.MessageBoxW(
            None,
            (
                "Administrator privileges are required to run this program.\n"
                "Please approve the UAC prompt and launch again."
            ),
            "DNF Auto-Down-Rank Automation Tool",
            0x00000010,
        )
    sys.exit(0)


def _build_elevation_command() -> tuple[str, str]:
    if getattr(sys, "frozen", False):
        executable = sys.executable
        parameters = subprocess.list2cmdline(sys.argv[1:])
        return executable, parameters

    script_path = str(Path(__file__).resolve())
    executable = sys.executable
    parameters = subprocess.list2cmdline([script_path, *sys.argv[1:]])
    return executable, parameters


def main() -> None:
    _ensure_admin_privileges()
    app = DnfAutomationApp()
    app.run()


if __name__ == "__main__":
    main()
