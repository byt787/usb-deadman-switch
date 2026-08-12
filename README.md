<div align="center">

# 🔌 usb-deadman-switch

### Pull the cable, lock the machine.

A tiny cross-platform Python watchdog that instantly **locks your screen — or shuts your PC down** — the moment a USB cable or drive is unplugged.

[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blue)](#)
[![Python](https://img.shields.io/badge/python-3.9%2B-yellow)](#)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![GUI](https://img.shields.io/badge/GUI-pygame-ff69b4)](#)

</div>

---

> ⚠️ **Use at your own risk.** This tool takes an action (lock or shutdown) based on USB events. Misconfiguration — e.g. `mode: any` on a machine with several USB peripherals, or `action: shutdown` combined with a twitchy cable — can lead to unexpected lock-outs or data loss from unsaved work. It's a supplementary security layer, not a replacement for disk encryption or a strong password.

## What is this?

This is a **USB deadman switch**, the same concept behind projects like [BusKill](https://buskill.in). Plug a USB stick into your laptop and tether it to your wrist with a cord. Stand up, get up to grab a coffee, or have your laptop snatched — the cable pulls out, and your machine locks (or powers off) instantly.

<div align="center">

![usb-lock GUI preview, showing the switch in the ON and OFF state](assets/gui_preview.png)

*A borderless, black 300×300px control panel — green means armed, gray means disabled.*

</div>

---

## ✨ Features

| | |
|---|---|
| 🔒 **Lock or shutdown** | Choose what happens on removal via `action: lock` or `action: shutdown` |
| ⚡ **Real-time detection** | WMI event watching on Windows, kernel netlink events on Linux — no laggy polling |
| 🎯 **Two trigger modes** | React to *any* USB device, or only a *specific* one by Vendor/Product ID |
| 🖥️ **Minimal GUI** | Optional borderless on/off switch — arm or disarm with one click |
| 🚀 **Autostart ready** | Ships with a systemd service (Linux) and Task Scheduler script (Windows) |
| 🧩 **Zero-config default** | Works out of the box with sane defaults, no `config.yaml` required |

---

## ⚙️ How It Works

<table>
<tr>
<td width="50%" valign="top">

### 🪟 Windows
`watcher_windows.py` uses **WMI event watching** (`__InstanceDeletionEvent`) to detect device removal essentially in real time — no missed events, even on fast unplug/replug. Locking calls `LockWorkStation()` from `user32.dll`, the exact function `Win + L` triggers internally. A legacy polling fallback kicks in automatically if event watching isn't available.

</td>
<td width="50%" valign="top">

### 🐧 Linux
`watcher_linux.py` uses **`pyudev`** to receive kernel netlink events for USB devices instantly, with zero polling. Locking tries a list of common session lockers in order — `loginctl lock-session`, `gnome-screensaver-command`, `xdg-screensaver`, `i3lock`, `swaylock`, and more — until one works.

</td>
</tr>
</table>

---

## 🎛️ Configuration

Copy the example config and adjust it:

```bash
cp config.example.yaml config.yaml
```

```yaml
# What to do when a matching USB removal is detected:
#   "lock"     -> lock the screen (default, safe)
#   "shutdown" -> shut the machine down immediately (DESTRUCTIVE)
action: lock

# "any"      -> triggers on ANY USB device removal (mouse, keyboard, stick, ...)
# "specific" -> only triggers on the device(s) listed below
mode: any

specific_devices:
  - vendor_id: "0781"
    product_id: "5567"

poll_interval: 1.0   # Windows only, fallback polling interval in seconds
lock_delay: 0        # seconds to wait before running the action
```

No `config.yaml`? No problem — sensible defaults (`action: lock`, `mode: any`) are used automatically.

<details>
<summary><strong>🔎 Finding a device's Vendor/Product ID</strong></summary>
<br>

* **Linux:** `lsusb` → format `Bus 001 Device 004: ID <vendor>:<product> ...`
* **Windows:** Device Manager → Device → Properties → Details → **"Hardware IDs"** (`VID_xxxx&PID_xxxx`)

</details>

---

## 🚀 Installation

### 1. Clone & install dependencies

```bash
git clone https://github.com/byt787/usb-deadman-switch.git
cd usb-deadman-switch
python -m venv .venv
```

<table>
<tr><th>Windows</th><th>Linux</th></tr>
<tr>
<td>

```powershell
.venv\Scripts\activate
pip install -r requirements-windows.txt
```

</td>
<td>

```bash
source .venv/bin/activate
pip install -r requirements-linux.txt
```

</td>
</tr>
</table>

> **Linux note:** `pyudev` requires `libudev` (present on virtually every distro by default). The user also needs permission to run the relevant lock command — normally the case on any standard desktop environment.

### 2. Test it manually

| Mode | Command |
|---|---|
| Console only | `python -m usb_lock.main` |
| GUI (on/off switch) | `python -m usb_lock.gui` |

The GUI opens a borderless, black 300×300px window with an on/off switch in the center. The watcher **always** runs in the background — the switch only decides whether a detected removal actually fires the configured action (**ON = green = armed**, **OFF = gray = disarmed**). Close via the small dot top-right, or hit `Esc`. Click + drag the background to move the window.

Unplug a USB device and watch it trigger. 🔌

### 3. Set up autostart

<table>
<tr><th>🐧 Linux (systemd --user)</th><th>🪟 Windows (Task Scheduler)</th></tr>
<tr>
<td>

```bash
bash install/install_linux.sh
```

Manage it:
```bash
systemctl --user status usb-lock.service
systemctl --user stop usb-lock.service
systemctl --user disable usb-lock.service
```

</td>
<td>

```powershell
powershell -ExecutionPolicy Bypass `
  -File install\install_windows_task.ps1
```

Runs silently at logon (`pythonw.exe`, no visible window). Manage via **Task Scheduler** (`taskschd.msc`) → `usb-lock`.

</td>
</tr>
</table>

---

## 📁 Project Structure

```text
usb-deadman-switch/
├── usb_lock/
│   ├── main.py                    # Console entry point
│   ├── gui.py                     # Pygame GUI: black square with on/off switch
│   ├── config.py                  # Loads & validates config.yaml
│   ├── lock.py                    # Platform-specific lock() / shutdown()
│   ├── watcher_windows.py         # WMI event watching
│   └── watcher_linux.py           # pyudev events
├── install/
│   ├── usb-lock.service           # systemd unit
│   ├── install_linux.sh           # Installs the systemd service
│   └── install_windows_task.ps1   # Installs the Task Scheduler task
├── assets/
│   └── gui_preview.png
├── config.example.yaml
├── requirements*.txt
└── run_windows.bat                # Manual test run on Windows
```

---

## 🛡️ Security Notes

* This is an **additional** security layer — not a replacement for full-disk encryption, a strong password/PIN, or an automatic screen-lock timeout.
* `mode: any` can cause unintended triggers (e.g. unplugging a hub with several devices at once). For a genuine deadman-switch setup, use `mode: specific` with one dedicated USB stick.
* `action: shutdown` is destructive — any unsaved work is lost. Stick with `action: lock` unless you have a specific reason to power off entirely.
* On Linux, lock reliability depends on which session locker is installed. If none of the commands in `lock.py` work on your setup, just add the right one for your desktop environment.

---

## 📄 License

MIT — see [LICENSE](LICENSE).
