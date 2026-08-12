"""Cross-platform screen locking and shutdown.

Windows: calls LockWorkStation() from user32.dll - exactly what Win+L
triggers internally. Shutdown uses the built-in `shutdown` command.

Linux: there's no single universal "Win+L". A series of common lock
commands is tried in order (systemd-logind, GNOME, generic
xdg-screensaver, i3lock, ...) until one succeeds. Shutdown uses
systemd (`systemctl poweroff`) with a couple of fallbacks.
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


# ------------------------------------------------------------------ Lock --
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
    cmd = [
        "/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession",
        "-suspend",
    ]
    return _try_command(cmd)


def lock_screen() -> bool:
    """Locks the screen for the currently running OS.

    Returns True if locking (probably) succeeded.
    """
    system = platform.system()
    if system == "Windows":
        return lock_windows()
    if system == "Linux":
        return lock_linux()
    if system == "Darwin":
        return lock_macos()
    raise RuntimeError(f"Unsupported operating system: {system}")


# -------------------------------------------------------------- Shutdown --
def shutdown_windows() -> bool:
    # /s = shutdown, /t 0 = no delay, /f = force-close running applications
    return _try_command(["shutdown", "/s", "/t", "0", "/f"])


def shutdown_linux() -> bool:
    candidates = [
        ["systemctl", "poweroff"],
        ["loginctl", "poweroff"],
        ["shutdown", "-h", "now"],
        ["poweroff"],
    ]
    for cmd in candidates:
        if _try_command(cmd):
            return True
    return False


def shutdown_macos() -> bool:
    return _try_command(["osascript", "-e", 'tell app "System Events" to shut down'])


def shutdown_system() -> bool:
    """Shuts down the machine for the currently running OS.

    Returns True if the shutdown command was (probably) issued successfully.
    Note: this is destructive - unsaved work will be lost. Consider using
    `action: lock` unless you specifically need a full shutdown.
    """
    system = platform.system()
    if system == "Windows":
        return shutdown_windows()
    if system == "Linux":
        return shutdown_linux()
    if system == "Darwin":
        return shutdown_macos()
    raise RuntimeError(f"Unsupported operating system: {system}")


# --------------------------------------------------------------- Dispatch --
def perform_action(action: str) -> bool:
    """Runs either lock_screen() or shutdown_system() based on `action`."""
    if action == "shutdown":
        return shutdown_system()
    if action == "lock":
        return lock_screen()
    raise ValueError(f"Unknown action: {action!r} (expected 'lock' or 'shutdown')")
