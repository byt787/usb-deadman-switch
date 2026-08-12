"""USB-Ueberwachung fuer Linux via pyudev (nutzt Kernel-Netlink-Events,
kein Polling noetig -> reagiert praktisch sofort)."""
from __future__ import annotations

from typing import Callable, Iterable

import pyudev


def _matches_specific(device: "pyudev.Device", specific_devices: Iterable[dict]) -> bool:
    vid = (device.get("ID_VENDOR_ID") or "").upper()
    pid = (device.get("ID_MODEL_ID") or "").upper()
    for entry in specific_devices:
        want_vid = str(entry.get("vendor_id", "")).upper()
        want_pid = str(entry.get("product_id", "")).upper()
        if want_vid and want_vid != vid:
            continue
        if want_pid and want_pid != pid:
            continue
        if want_vid or want_pid:
            return True
    return False


def watch(
    on_remove: Callable[["pyudev.Device"], None],
    mode: str = "any",
    specific_devices: Iterable[dict] | None = None,
    poll_interval: float = 1.0,  # ungenutzt unter Linux, nur fuer einheitliche Signatur
) -> None:
    """Blockiert und ruft on_remove(device) bei jeder erkannten USB-Entfernung auf."""
    specific_devices = list(specific_devices or [])

    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem="usb")

    for device in iter(monitor.poll, None):
        if device.action != "remove":
            continue

        if mode == "specific" and not _matches_specific(device, specific_devices):
            continue

        on_remove(device)
