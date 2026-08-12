"""USB-Ueberwachung fuer Windows.

Es wird bewusst ein Polling-Ansatz via WMI (Win32_PnPEntity) genutzt statt
auf die Event-Type-Konstanten von Win32_DeviceChangeEvent zu vertrauen -
das ist robuster und einfacher zuverlaessig zu testen.
"""
from __future__ import annotations

import time
from typing import Callable, Iterable, Set

import pythoncom
import wmi


def _get_usb_device_ids(conn: "wmi.WMI") -> Set[str]:
    ids = set()
    for dev in conn.Win32_PnPEntity():
        device_id = dev.DeviceID or ""
        if "USB" in device_id.upper():
            ids.add(device_id)
    return ids


def _matches_specific(device_id: str, specific_devices: Iterable[dict]) -> bool:
    device_id_upper = device_id.upper()
    for entry in specific_devices:
        vid = str(entry.get("vendor_id", "")).upper()
        pid = str(entry.get("product_id", "")).upper()
        if vid and f"VID_{vid}" not in device_id_upper:
            continue
        if pid and f"PID_{pid}" not in device_id_upper:
            continue
        if vid or pid:
            return True
    return False


def watch(
    on_remove: Callable[[Set[str]], None],
    mode: str = "any",
    specific_devices: Iterable[dict] | None = None,
    poll_interval: float = 1.0,
) -> None:
    """Blockiert und ruft on_remove(removed_ids) bei jeder erkannten USB-Entfernung auf."""
    specific_devices = list(specific_devices or [])

    # WMI braucht in jedem Thread eine eigene COM-Initialisierung.
    pythoncom.CoInitialize()
    try:
        conn = wmi.WMI()
        known = _get_usb_device_ids(conn)

        while True:
            time.sleep(poll_interval)
            current = _get_usb_device_ids(conn)
            removed = known - current
            known = current

            if not removed:
                continue

            if mode == "specific":
                removed = {
                    dev_id for dev_id in removed
                    if _matches_specific(dev_id, specific_devices)
                }

            if removed:
                on_remove(removed)
    finally:
        pythoncom.CoUninitialize()
