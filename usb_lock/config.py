"""Konfigurations-Handling fuer usb-lock."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Dict

DEFAULT_CONFIG_PATHS = [
    "config.yaml",
    os.path.expanduser("~/.config/usb-lock/config.yaml"),
]


@dataclass
class Config:
    mode: str = "any"  # "any" oder "specific"
    specific_devices: List[Dict[str, str]] = field(default_factory=list)
    poll_interval: float = 1.0
    lock_delay: float = 0.0

    @classmethod
    def load(cls, path: str | None = None) -> "Config":
        candidates = [path] if path else DEFAULT_CONFIG_PATHS
        for candidate in candidates:
            if candidate and os.path.isfile(candidate):
                return cls._from_file(candidate)
        # Keine Config gefunden -> Defaults verwenden
        return cls()

    @classmethod
    def _from_file(cls, path: str) -> "Config":
        import yaml

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return cls(
            mode=data.get("mode", "any"),
            specific_devices=data.get("specific_devices", []) or [],
            poll_interval=float(data.get("poll_interval", 1.0)),
            lock_delay=float(data.get("lock_delay", 0.0)),
        )
