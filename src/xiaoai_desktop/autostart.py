from __future__ import annotations

import sys
from pathlib import Path


APP_NAME = "XiaoAiDesktop"


def startup_script_path() -> Path:
    if sys.platform != "win32":
        return Path.home() / ".config" / "autostart" / f"{APP_NAME}.cmd"
    return Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / f"{APP_NAME}.cmd"


def enable_autostart() -> None:
    path = startup_script_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    command = _launch_command()
    path.write_text(
        "@echo off\n"
        f"{command} --minimized\n",
        encoding="utf-8",
    )


def disable_autostart() -> None:
    path = startup_script_path()
    if path.exists():
        path.unlink()


def is_autostart_enabled() -> bool:
    return startup_script_path().exists()


def _launch_command() -> str:
    if getattr(sys, "frozen", False):
        return f"\"{Path(sys.executable)}\""
    return f"\"{Path(sys.executable)}\" -m xiaoai_desktop"
