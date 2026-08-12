#!/usr/bin/env bash
# Installiert usb-lock als systemd --user Service, der beim Login startet.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_DIR="$HOME/.config/systemd/user"

echo "Repo-Verzeichnis: $REPO_DIR"

mkdir -p "$UNIT_DIR"
sed "s#%h/usb-lock#$REPO_DIR#" "$REPO_DIR/install/usb-lock.service" > "$UNIT_DIR/usb-lock.service"

systemctl --user daemon-reload
systemctl --user enable --now usb-lock.service

echo "Fertig. Status pruefen mit: systemctl --user status usb-lock.service"
echo "Logs ansehen mit:          journalctl --user -u usb-lock.service -f"
