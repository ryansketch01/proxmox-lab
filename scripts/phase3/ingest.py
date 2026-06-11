#!/usr/bin/env python3
"""
ingest.py — Malware Sample Ingestion Script
Phase 3, proxmox-lab

Usage:
    sudo python3 ingest.py <path_to_sample> [options]

Options:
    --family    Malware family/type (ransomware, trojan, loader, stealer, rat, wiper, dropper, unknown)
    --source    Where the sample came from (e.g. MalwareBazaar, manual, theZoo)
    --tags      Comma-separated tags (e.g. "LockBit,x64,PE32")
    --notes     Free-text notes
    --no-splunk Skip Splunk forwarding

Example:
    sudo python3 ingest.py /tmp/evil.exe --family ransomware --source MalwareBazaar --tags "LockBit,x64"
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────

REPO_ROOT   = "/opt/malware-lab"
CATALOG     = os.path.join(REPO_ROOT, "catalog", "catalog.json")
ZIP_PASS    = "infected"

# Frank's LAN IP — nginx reverse proxy forwarding to Splunk HEC on port 8088
# Update this if Frank's IP changes
SPLUNK_HEC_URL   = "http://192.168.1.66:8088/services/collector/event"
SPLUNK_HEC_TOKEN = "6f32239e-d3ce-44d1-a9ea-46d845de7ddd"   # Paste your malware-lab-hec token here (from Bitwarden)
SPLUNK_INDEX     = "malware-lab"
SPLUNK_SOURCETYPE = "malware:catalog"

VALID_FAMILIES = [
    "ransomware", "trojan", "loader", "stealer",
    "rat", "wiper", "dropper", "unknown"
]

# ── Hashing ───────────────────────────────────────────────────────────────────

def hash_file(path: str) -> dict:
    """Compute MD5, SHA1, and SHA256 of a file."""
    md5    = hashlib.md5()
    sha1   = hashlib.sha1()
    sha256 = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            md5.update(chunk)
            sha1.update(chunk)
            sha256.update(chunk)

    return {
        "md5":    md5.hexdigest(),
        "sha1":   sha1.hexdigest(),
        "sha256": sha256.hexdigest(),
    }

# ── Catalog ───────────────────────────────────────────────────────────────────

def load_catalog() -> list:
    if not os.path.exists(CATALOG):
        return []
    with open(CATALOG, "r") as f:
        return json.load(f)

def save_catalog(catalog: list) -> None:
    with open(CATALOG, "w") as f:
        json.dump(catalog, f, indent=2)

def already_ingested(sha256: str, catalog: list) -> bool:
    return any(entry["sha256"] == sha256 for entry in catalog)

# ── Archiving ─────────────────────────────────────────────────────────────────

def zip_sample(src_path: str, dest_dir: str, sha256: str) -> str:
    """
    Zip a sample with password 'infected', named by its SHA256 hash.
    Returns the path to the created zip file.
    """
    zip_name = f"{sha256}.zip"
    zip_path = os.path.join(dest_dir, zip_name)

    result = subprocess.run(
        ["zip", "-P", ZIP_PASS, "-j", zip_path, src_path],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"zip failed: {result.stderr.strip()}")

    return zip_path

# ── Splunk ────────────────────────────────────────────────────────────────────

def forward_to_splunk(record: dict) -> bool:
    """Send catalog record to Splunk HEC. Returns True on success."""
    if not SPLUNK_HEC_TOKEN:
        print("[!] SPLUNK_HEC_TOKEN not set — skipping Splunk forward.")
        return False

    payload = json.dumps({
        "index":      SPLUNK_INDEX,
        "sourcetype": SPLUNK_SOURCETYPE,
        "event":      record,
        "time":       datetime.now(timezone.utc).timestamp(),
    }).encode("utf-8")

    req = urllib.request.Request(
        SPLUNK_HEC_URL,
        data=payload,
        headers={
            "Authorization": f"Splunk {SPLUNK_HEC_TOKEN}",
            "Content-Type":  "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            result = json.loads(body)
            if result.get("text") == "Success":
                return True
            else:
                print(f"[!] Splunk HEC returned: {body}")
                return False
    except urllib.error.URLError as e:
        print(f"[!] Could not reach Splunk HEC: {e}")
        return False

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Ingest a malware sample into the local repository.")
    parser.add_argument("sample",               help="Path to the raw sample file")
    parser.add_argument("--family",             default="unknown", choices=VALID_FAMILIES,
                                                help="Malware family/type")
    parser.add_argument("--source",             default="manual",  help="Sample source")
    parser.add_argument("--tags",               default="",        help="Comma-separated tags")
    parser.add_argument("--notes",              default="",        help="Free-text notes")
    parser.add_argument("--no-splunk",          action="store_true", help="Skip Splunk forwarding")
    args = parser.parse_args()

    # ── Validate input ────────────────────────────────────────────────────────

    sample_path = os.path.abspath(args.sample)
    if not os.path.isfile(sample_path):
        print(f"[!] File not found: {sample_path}")
        sys.exit(1)

    if os.geteuid() != 0:
        print("[!] Run as root (sudo) — required to write to /opt/malware-lab/")
        sys.exit(1)

    # ── Hash ──────────────────────────────────────────────────────────────────

    original_name = os.path.basename(sample_path)
    print(f"[*] Hashing {original_name}...")
    hashes = hash_file(sample_path)
    sha256 = hashes["sha256"]
    print(f"    SHA256: {sha256}")
    print(f"    MD5:    {hashes['md5']}")
    print(f"    SHA1:   {hashes['sha1']}")

    # ── Duplicate check ───────────────────────────────────────────────────────

    catalog = load_catalog()
    if already_ingested(sha256, catalog):
        print(f"[!] Sample already in catalog (SHA256: {sha256}). Skipping.")
        sys.exit(0)

    # ── Archive ───────────────────────────────────────────────────────────────

    dest_dir = os.path.join(REPO_ROOT, "samples", args.family)
    os.makedirs(dest_dir, exist_ok=True)

    print(f"[*] Archiving to {dest_dir}/...")
    zip_path = zip_sample(sample_path, dest_dir, sha256)
    print(f"[+] Archived: {zip_path}")

    # Remove raw sample after successful zip
    os.remove(sample_path)
    print(f"[*] Raw sample deleted: {sample_path}")

    # ── Build catalog record ──────────────────────────────────────────────────

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    record = {
        "sha256":            sha256,
        "md5":               hashes["md5"],
        "sha1":              hashes["sha1"],
        "filename_original": original_name,
        "family":            args.family,
        "source":            args.source,
        "date_ingested":     datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "tags":              tags,
        "iocs":              [],
        "zip_path":          zip_path,
        "notes":             args.notes,
    }

    catalog.append(record)
    save_catalog(catalog)
    print(f"[+] Catalog updated ({len(catalog)} total samples)")

    # ── Splunk ────────────────────────────────────────────────────────────────

    if not args.no_splunk:
        print("[*] Forwarding to Splunk...")
        ok = forward_to_splunk(record)
        if ok:
            print("[+] Splunk: event received")
        else:
            print("[!] Splunk forward failed — record still saved locally")

    # ── Done ──────────────────────────────────────────────────────────────────

    print()
    print(f"[+] Ingestion complete: {original_name} → {args.family}/{sha256}.zip")


if __name__ == "__main__":
    main()
