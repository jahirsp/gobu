#!/usr/bin/env bash
#
# install.sh - Instala gobu como comando global (tipo nmap, gobuster, etc)
#
# Uso:
#   sudo ./install.sh
#
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_FILE="$REPO_DIR/gobu.py"
INSTALL_PATH="/usr/local/bin/gobu"

# --- chequeos básicos ---

if [ "$EUID" -ne 0 ]; then
    echo "[!] Este script necesita permisos de root (para escribir en /usr/local/bin)."
    echo "    Corré: sudo ./install.sh"
    exit 1
fi

if [ ! -f "$SRC_FILE" ]; then
    echo "[!] No encontré gobu.py en $REPO_DIR"
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "[!] No encontré python3 en el PATH. Instalalo antes de continuar."
    exit 1
fi

# --- instalación ---

echo "[*] Copiando gobu.py -> $INSTALL_PATH"
cp "$SRC_FILE" "$INSTALL_PATH"
chmod +x "$INSTALL_PATH"

echo "[*] Verificando dependencias externas (gobuster, curl)..."
faltan=()
for bin in gobuster curl; do
    if ! command -v "$bin" >/dev/null 2>&1; then
        faltan+=("$bin")
    fi
done

if [ ${#faltan[@]} -gt 0 ]; then
    echo "[!] Atención: no encontré en el PATH: ${faltan[*]}"
    echo "    gobu se instaló igual, pero no va a funcionar hasta que los instales."
    echo "    En Debian/Kali/Ubuntu por ejemplo:"
    echo "      sudo apt install gobuster curl"
fi

echo
echo "[+] Listo. Ya podés usar el comando 'gobu' desde cualquier lado:"
echo "      gobu <ip>"
echo "      gobu <dominio>"
echo "      gobu <ip> <dominio>"
echo
echo "    Para desinstalar: sudo ./uninstall.sh"
