"""Plattformuebergreifende Bildschirmsperre.

Windows: ruft LockWorkStation() aus user32.dll auf - das ist exakt das,
was auch Win+L intern ausloest.

Linux: es gibt kein einheitliches "Win+L". Es wird eine Reihe gaengiger
Sperrbefehle der Reihe nach probiert (systemd-logind, GNOME, generisches
xdg-screensaver, i3lock, ...), bis einer erfolgreich ist.
"""
from __future__ import annotations

import platform
import subprocess
import shutil


def _try_command(cmd: list[str], timeout: float = 5.0) -> bool:
    exe = cmd[0]
    if shutil.which(exe) is None:
        return False
    try:
        result = subprocess.run(
            cmd, timeout=timeout, check=False,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0
    except Exception:
        return False


def lock_windows() -> bool:
    import ctypes

    try:
        ctypes.windll.user32.LockWorkStation()
        return True
    except Exception:
        return False


def lock_linux() -> bool:
    candidates = [
        ["loginctl", "lock-session"],
        ["gnome-screensaver-command", "-l"],
        ["dm-tool", "lock"],
        ["xdg-screensaver", "lock"],
        ["i3lock"],
        ["swaylock"],
        ["xscreensaver-command", "-lock"],
        ["cinnamon-screensaver-command", "-l"],
        ["xfce4-screensaver-command", "-l"],
        ["light-locker-command", "-l"],
        ["betterlockscreen", "-l"],
    ]
    for cmd in candidates:
        if _try_command(cmd):
            return True
    return False


def lock_macos() -> bool:
    # Sperrt den Bildschirm auf macOS via CGSession.
    cmd = [
        "/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession",
        "-suspend",
    ]
    return _try_command(cmd)


def lock_screen() -> bool:
    """Sperrt den Bildschirm passend zum laufenden Betriebssystem.

    Gibt True zurueck, wenn (vermutlich) erfolgreich gesperrt wurde.
    """
    system = platform.system()
    if system == "Windows":
        return lock_windows()
    if system == "Linux":
        return lock_linux()
    if system == "Darwin":
        return lock_macos()
    raise RuntimeError(f"Nicht unterstuetztes Betriebssystem: {system}")
