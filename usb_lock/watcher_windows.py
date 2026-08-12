"""USB monitoring for Windows.

Primarily uses WMI event watching (__InstanceDeletionEvent on
Win32_PnPEntity). This is much more reliable than manual polling,
because the diffing is handled by the WMI engine itself instead of
re-reading and comparing ALL PnP devices (often 200+) in Python on
every tick - which is exactly what causes missed events on a fast
unplug/replug, since a single poll cycle can take longer than the
plugging action itself.

If event watching fails for some reason on a given system (e.g. WMI
permissions, a very old Windows version), the code automatically falls
back to the old polling method.
"""
from __future__ import annotations

import time
from typing import Callable, Iterable, Set

import pythoncom
import wmi


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


def _emit(on_remove, mode, specific_devices, device_id: str) -> None:
    if "USB" not in (device_id or "").upper():
        return
    if mode == "specific" and not _matches_specific(device_id, specific_devices):
        return
    on_remove({device_id})


# ----------------------------------------------------------- Event-based --
def _watch_events(conn, on_remove, mode, specific_devices, delay_secs: float) -> None:
    """Uses WMI __InstanceDeletionEvent - reacts essentially in real time."""
    deletion_watcher = conn.Win32_PnPEntity.watch_for(
        notification_type="deletion",
        delay_secs=max(0.5, delay_secs),
    )
    while True:
        event = deletion_watcher()  # blocks until the next deletion event
        device_id = getattr(event, "DeviceID", "") or ""
        _emit(on_remove, mode, specific_devices, device_id)


# --------------------------------------------------------------- Fallback --
def _get_usb_device_ids(conn: "wmi.WMI") -> Set[str]:
    ids = set()
    for dev in conn.Win32_PnPEntity():
        device_id = dev.DeviceID or ""
        if "USB" in device_id.upper():
            ids.add(device_id)
    return ids


def _watch_polling(conn, on_remove, mode, specific_devices, poll_interval: float) -> None:
    """Old method: full enumeration + diff. Fallback only."""
    known = _get_usb_device_ids(conn)
    while True:
        time.sleep(poll_interval)
        current = _get_usb_device_ids(conn)
        removed = known - current
        known = current
        for device_id in removed:
            _emit(on_remove, mode, specific_devices, device_id)


# ------------------------------------------------------------------- API --
def watch(
    on_remove: Callable[[Set[str]], None],
    mode: str = "any",
    specific_devices: Iterable[dict] | None = None,
    poll_interval: float = 1.0,
) -> None:
    """Blocks and calls on_remove({device_id}) for every detected USB removal."""
    specific_devices = list(specific_devices or [])

    # WMI needs its own COM initialization in every thread.
    pythoncom.CoInitialize()
    try:
        conn = wmi.WMI()
        try:
            _watch_events(conn, on_remove, mode, specific_devices, poll_interval)
        except Exception as exc:
            print(
                f"[usb-lock] WMI event watching failed ({exc}), "
                "falling back to polling.",
                flush=True,
            )
            _watch_polling(conn, on_remove, mode, specific_devices, poll_interval)
    finally:
        pythoncom.CoUninitialize()
