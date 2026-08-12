#!/usr/bin/env bash
# Installs usb-lock as a systemd --user service that starts on login.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_DIR="$HOME/.config/systemd/user"

echo "Repo directory: $REPO_DIR"

mkdir -p "$UNIT_DIR"
sed "s#%h/usb-lock#$REPO_DIR#" "$REPO_DIR/install/usb-lock.service" > "$UNIT_DIR/usb-lock.service"

systemctl --user daemon-reload
systemctl --user enable --now usb-lock.service

echo "Done. Check status with: systemctl --user status usb-lock.service"
echo "View logs with:          journalctl --user -u usb-lock.service -f"
