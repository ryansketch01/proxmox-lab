#!/usr/bin/env bash
# Phase 3 — Malware Sample Repository Setup
# Run once on REMnux as root: sudo bash setup_repo.sh

set -e

REPO_ROOT="/opt/malware-lab"

echo "[*] Creating malware sample repository at $REPO_ROOT"

mkdir -p "$REPO_ROOT/samples/ransomware"
mkdir -p "$REPO_ROOT/samples/trojan"
mkdir -p "$REPO_ROOT/samples/loader"
mkdir -p "$REPO_ROOT/samples/stealer"
mkdir -p "$REPO_ROOT/samples/rat"
mkdir -p "$REPO_ROOT/samples/wiper"
mkdir -p "$REPO_ROOT/samples/dropper"
mkdir -p "$REPO_ROOT/samples/unknown"
mkdir -p "$REPO_ROOT/catalog"
mkdir -p "$REPO_ROOT/scripts"

# Initialize empty catalog if it doesn't exist
CATALOG="$REPO_ROOT/catalog/catalog.json"
if [ ! -f "$CATALOG" ]; then
    echo "[]" > "$CATALOG"
    echo "[*] Initialized empty catalog at $CATALOG"
fi

# Lock down permissions — only root can read samples
chmod 700 "$REPO_ROOT/samples"
chmod 700 "$REPO_ROOT/catalog"
chown -R root:root "$REPO_ROOT"

# Ensure zip is available (used for password-protected archiving)
if ! command -v zip &>/dev/null; then
    echo "[*] Installing zip..."
    apt-get install -y zip
fi

echo ""
echo "[+] Repository structure created:"
find "$REPO_ROOT" -type d | sort
echo ""
echo "[+] Done. Deploy scripts to $REPO_ROOT/scripts/ and run ingest.py to add samples."
