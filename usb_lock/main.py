"""usb-lock: sperrt den Bildschirm, sobald ein USB-Geraet entfernt wird.

Aufruf:
    python -m usb_lock.main [--config /pfad/zur/config.yaml]
"""
from __future__ import annotations

import argparse
import platform
import sys
import time

from usb_lock.config import Config
from usb_lock.lock import lock_screen


def _log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def _handle_removal(cfg: Config, info) -> None:
    _log(f"USB-Geraet entfernt: {info}")
    if cfg.lock_delay > 0:
        _log(f"Warte {cfg.lock_delay}s vor dem Sperren ...")
        time.sleep(cfg.lock_delay)
    ok = lock_screen()
    if ok:
        _log("Bildschirm gesperrt.")
    else:
        _log("WARNUNG: Sperren fehlgeschlagen oder Erfolg nicht feststellbar.")


def run(config_path: str | None = None) -> None:
    cfg = Config.load(config_path)
    system = platform.system()

    _log(f"usb-lock gestartet (OS={system}, mode={cfg.mode})")

    if system == "Windows":
        from usb_lock import watcher_windows as watcher
    elif system == "Linux":
        from usb_lock import watcher_linux as watcher
    else:
        _log(f"Betriebssystem '{system}' wird nicht unterstuetzt (nur Windows/Linux).")
        sys.exit(1)

    try:
        watcher.watch(
            on_remove=lambda info: _handle_removal(cfg, info),
            mode=cfg.mode,
            specific_devices=cfg.specific_devices,
            poll_interval=cfg.poll_interval,
        )
    except KeyboardInterrupt:
        _log("Beendet durch Benutzer.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sperrt den Bildschirm bei USB-Entfernung.")
    parser.add_argument(
        "--config", "-c", default=None,
        help="Pfad zur config.yaml (Standard: ./config.yaml oder ~/.config/usb-lock/config.yaml)",
    )
    args = parser.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
