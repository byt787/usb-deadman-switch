"""usb-lock: locks the screen (or shuts down) as soon as a USB device
is removed.

Usage:
    python -m usb_lock.main [--config /path/to/config.yaml]
"""
from __future__ import annotations

import argparse
import platform
import sys
import time

from usb_lock.config import Config
from usb_lock.lock import perform_action


def _log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def _handle_removal(cfg: Config, info) -> None:
    _log(f"USB device removed: {info}")
    if cfg.lock_delay > 0:
        _log(f"Waiting {cfg.lock_delay}s before {cfg.action} ...")
        time.sleep(cfg.lock_delay)
    ok = perform_action(cfg.action)
    if ok:
        _log(f"Action '{cfg.action}' executed successfully.")
    else:
        _log(f"WARNING: action '{cfg.action}' failed or success could not be confirmed.")


def run(config_path: str | None = None) -> None:
    cfg = Config.load(config_path)
    system = platform.system()

    _log(f"usb-lock started (OS={system}, mode={cfg.mode}, action={cfg.action})")

    if system == "Windows":
        from usb_lock import watcher_windows as watcher
    elif system == "Linux":
        from usb_lock import watcher_linux as watcher
    else:
        _log(f"Operating system '{system}' is not supported (Windows/Linux only).")
        sys.exit(1)

    try:
        watcher.watch(
            on_remove=lambda info: _handle_removal(cfg, info),
            mode=cfg.mode,
            specific_devices=cfg.specific_devices,
            poll_interval=cfg.poll_interval,
        )
    except KeyboardInterrupt:
        _log("Stopped by user.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Locks the screen (or shuts down) on USB removal.")
    parser.add_argument(
        "--config", "-c", default=None,
        help="Path to config.yaml (default: ./config.yaml or ~/.config/usb-lock/config.yaml)",
    )
    args = parser.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
