# usb-deadman-switch

> Pull the cable, lock the machine.

Automatically locks the screen as soon as a USB device is unplugged — on Windows (equivalent to `Win + L`) and Linux.

> ⚠️ **Use at your own risk.** This tool locks your screen based on USB events. Misconfiguration (e.g. `mode: any` on a machine with several USB peripherals) could lead to unexpected lock-outs. It is a supplementary security layer, not a replacement for disk encryption or a strong password.

The concept is known as a **"USB deadman switch"**, similar to [BusKill](https://buskill.in). You plug in a USB stick, for example, and attach it to your wrist with a cord. If you stand up or someone pulls the laptop away, the cable disconnects and the computer immediately locks.

## Preview

The GUI is a borderless, black 300×300px window with an On/Off switch in the center — green when armed, gray when disabled:

![usb-lock GUI preview, showing the switch in the ON and OFF state](assets/gui_preview.png)

## How It Works

* **Windows**: `usb_lock/watcher_windows.py` polls the list of connected USB devices via WMI approximately every 1 second and detects changes. When locking, it calls `LockWorkStation()` from `user32.dll` — the same function triggered internally by `Win + L`.
* **Linux**: `usb_lock/watcher_linux.py` uses `pyudev` to receive kernel netlink events for USB devices in real time (no polling required). To lock the screen, it tries the first working command from a list of common screensaver/session lockers (`loginctl lock-session`, `gnome-screensaver-command`, `xdg-screensaver`, `i3lock`, `swaylock`, ...).

## Two Modes

* `mode: any` (default) — locks whenever **any USB device is removed**. Be careful: this also triggers when you unplug something like a wired mouse.
* `mode: specific` — locks only when one of the devices listed in `config.yaml` (by Vendor/Product ID) is removed. Recommended for the **"USB key attached to your wrist"** setup.

## Installation

### 1. Clone the Repository and Install Dependencies

```bash
git clone https://github.com/byt787/usb-deadman-switch.git
cd usb-deadman-switch
python -m venv .venv
```

**Windows:**

```powershell
.venv\Scripts\activate
pip install -r requirements-windows.txt
```

**Linux:**

```bash
source .venv/bin/activate
pip install -r requirements-linux.txt
```

> **Linux note:** `pyudev` requires `libudev` (already available on virtually every distribution). The user must also have permission to execute the respective lock command (this is normally the case on most desktop environments).

### 2. Create the Configuration (Optional)

```bash
cp config.example.yaml config.yaml
```

Adjust `mode`, and if necessary `specific_devices`, `poll_interval`, and `lock_delay`.

Without a `config.yaml`, the default values are used (`mode: any`).

### Finding the Vendor/Product ID

* **Linux:** `lsusb` (format: `Bus 001 Device 004: ID <vendor>:<product> ...`)
* **Windows:** Device Manager → Device → Properties → Details → **"Hardware IDs"** (`VID_xxxx&PID_xxxx`)

### 3. Test Manually

**Without GUI (console only):**

```bash
python -m usb_lock.main
```

**With GUI (black square with an On/Off switch):**

```bash
python -m usb_lock.gui
```

This opens a borderless black 300×300px window with an On/Off switch in the center. The USB watcher always runs in the background; the switch only determines whether a detected USB removal actually locks the screen: **ON (green)** or **OFF (gray)**.

A small dot in the top-right corner, or `Esc`, closes the window. Click and drag the background to move the window.

Unplug a USB device and observe the console/logs or the switch.

### 4. Set Up Autostart

**Linux (systemd --user):**

```bash
bash install/install_linux.sh
```

Afterwards, it will start automatically at every login. Manage it with:

```bash
systemctl --user status usb-lock.service
systemctl --user stop usb-lock.service
systemctl --user disable usb-lock.service
```

**Windows (Task Scheduler):**

```powershell
powershell -ExecutionPolicy Bypass -File install\install_windows_task.ps1
```

This creates a scheduled task that starts in the background (`pythonw.exe`, no visible window) whenever you log in.

Manage it through **Task Scheduler** (`taskschd.msc`) under the name `usb-lock`.

## Project Structure

```text
usb-deadman-switch/
├── usb_lock/
│   ├── main.py                    # Entry point (console), connects config + watcher + lock
│   ├── gui.py                     # Pygame GUI: black square with On/Off switch
│   ├── config.py                  # Loads config.yaml
│   ├── lock.py                    # Platform-specific screen locking
│   ├── watcher_windows.py         # WMI polling
│   └── watcher_linux.py           # pyudev events
├── install/
│   ├── usb-lock.service           # systemd unit
│   ├── install_linux.sh           # Installs the systemd service
│   └── install_windows_task.ps1  # Installs the Task Scheduler task
├── assets/
│   └── gui_preview.png            # Screenshot used in this README
├── config.example.yaml
├── requirements*.txt
└── run_windows.bat                # Manual test run on Windows
```

## Security Notes

* This tool is an **additional security mechanism**, not a replacement for full-disk encryption, a secure password/PIN, or an automatic screen-lock timeout.
* `mode: any` can cause unintended locks (for example, when unplugging a USB hub with multiple connected devices). For the **deadman-switch** use case, `mode: specific` with a dedicated USB stick is recommended.
* On Linux, the reliability of the locking mechanism depends on which session locker is installed on the system. If none of the commands listed in `lock.py` work, simply add the appropriate command for your desktop environment.

## License

MIT — see `LICENSE`.
