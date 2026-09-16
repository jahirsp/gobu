#!/usr/bin/env bash
#
# uninstall.sh - Quita el comando gobu del sistema
#
set -euo pipefail

INSTALL_PATH="/usr/local/bin/gobu"

if [ "$EUID" -ne 0 ]; then
    echo "[!] Este script necesita permisos de root."
    echo "    Corré: sudo ./uninstall.sh"
    exit 1
fi

if [ -f "$INSTALL_PATH" ]; then
    rm -f "$INSTALL_PATH"
    echo "[+] gobu desinstalado ($INSTALL_PATH eliminado)."
else
    echo "[i] No encontré $INSTALL_PATH, no había nada que desinstalar."
fi
