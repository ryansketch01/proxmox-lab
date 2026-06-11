#!/usr/bin/env python3
"""
thezoo_fetch.py — theZoo Sample Fetcher
Phase 3, proxmox-lab

Walks the local theZoo clone at /opt/theZoo/malware/Binaries/,
unzips each sample using its .pass file, and passes it through
ingest.py into the malware-lab repository.

Usage:
    sudo python3 thezoo_fetch.py [options]

Options:
    --limit     Max number of samples to ingest (default: 5)
    --name      Ingest a specific sample by folder name (e.g. Artemis)
    --list      List all available samples without ingesting
    --dry-run   Show what would be ingested without doing it
    --no-splunk Skip Splunk forwarding during ingest

Examples:
    sudo python3 thezoo_fetch.py --list
    sudo python3 thezoo_fetch.py --limit 5
    sudo python3 thezoo_fetch.py --name Artemis
    sudo python3 thezoo_fetch.py --limit 10 --dry-run
"""

import argparse
import os
import shutil
import subprocess
import sys

# ── Config ────────────────────────────────────────────────────────────────────

THEZOO_BINARIES = "/opt/theZoo/malware/Binaries"
INGEST_SCRIPT   = "/opt/malware-lab/scripts/ingest.py"
TMP_DIR         = "/tmp/thezoo_fetch"

# Map theZoo folder name prefixes to our local family taxonomy
FAMILY_MAP = {
    "ransomware": "ransomware",
    "ransom":     "ransomware",
    "locker":     "ransomware",
    "wanna":      "ransomware",
    "crypto":     "ransomware",
    "rat":        "rat",
    "backdoor":   "rat",
    "remote":     "rat",
    "stealer":    "stealer",
    "spy":        "stealer",
    "banker":     "stealer",
    "infostealer":"stealer",
    "trojan":     "trojan",
    "virus":      "trojan",
    "worm":       "trojan",
    "loader":     "loader",
    "dropper":    "dropper",
    "drop":       "dropper",
    "wiper":      "wiper",
    "destroyer":  "wiper",
    "bat":        "dropper",
    "android":    "trojan",
}

def map_family(folder_name: str) -> str:
    """Map theZoo folder name to our local family taxonomy."""
    lower = folder_name.lower()
    for keyword, family in FAMILY_MAP.items():
        if keyword in lower:
            return family
    return "unknown"

# ── Discovery ─────────────────────────────────────────────────────────────────

def get_all_samples() -> list:
    """Return list of (folder_name, folder_path) tuples for all theZoo samples."""
    samples = []
    if not os.path.isdir(THEZOO_BINARIES):
        print(f"[!] theZoo Binaries directory not found: {THEZOO_BINARIES}")
        sys.exit(1)

    for entry in sorted(os.listdir(THEZOO_BINARIES)):
        folder_path = os.path.join(THEZOO_BINARIES, entry)
        if not os.path.isdir(folder_path):
            continue

        # Verify it has the expected files
        files = os.listdir(folder_path)
        has_zip  = any(f.endswith(".zip")  for f in files)
        has_pass = any(f.endswith(".pass") for f in files)

        if has_zip and has_pass:
            samples.append((entry, folder_path))

    return samples

# ── Ingest ────────────────────────────────────────────────────────────────────

def ingest_sample(folder_name: str, folder_path: str, no_splunk: bool) -> bool:
    """Unzip a theZoo sample and pass it through ingest.py."""

    files     = os.listdir(folder_path)
    zip_file  = next((f for f in files if f.endswith(".zip")),  None)
    pass_file = next((f for f in files if f.endswith(".pass")), None)

    if not zip_file or not pass_file:
        print(f"  [!] Missing zip or pass file in {folder_name}")
        return False

    zip_path  = os.path.join(folder_path, zip_file)
    pass_path = os.path.join(folder_path, pass_file)

    # Read password
    with open(pass_path, "r") as f:
        password = f.read().strip()

    # Extract to temp dir
    extract_dir = os.path.join(TMP_DIR, folder_name)
    os.makedirs(extract_dir, exist_ok=True)

    result = subprocess.run(
        ["unzip", "-P", password, "-o", zip_path, "-d", extract_dir],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"  [!] Unzip failed: {result.stderr.strip()}")
        shutil.rmtree(extract_dir, ignore_errors=True)
        return False

    # Find extracted files (skip hidden/system files)
    extracted = [
        os.path.join(extract_dir, f)
        for f in os.listdir(extract_dir)
        if not f.startswith(".")
    ]

    if not extracted:
        print(f"  [!] No files found after unzip")
        shutil.rmtree(extract_dir, ignore_errors=True)
        return False

    # Ingest each extracted file
    family   = map_family(folder_name)
    all_ok   = True

    for raw_sample in extracted:
        cmd = [
            "python3", INGEST_SCRIPT,
            raw_sample,
            "--family", family,
            "--source", "theZoo",
            "--tags",   folder_name,
            "--notes",  f"theZoo sample: {folder_name}",
        ]
        if no_splunk:
            cmd.append("--no-splunk")

        r = subprocess.run(cmd, text=True)
        if r.returncode != 0:
            all_ok = False

    # Clean up temp extract dir
    shutil.rmtree(extract_dir, ignore_errors=True)
    return all_ok

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Ingest samples from local theZoo clone.")
    parser.add_argument("--limit",     type=int, default=5,    help="Max samples to ingest (default: 5)")
    parser.add_argument("--name",      default="",             help="Ingest specific sample by folder name")
    parser.add_argument("--list",      action="store_true",    help="List all available samples")
    parser.add_argument("--dry-run",   action="store_true",    help="Show what would be ingested")
    parser.add_argument("--no-splunk", action="store_true",    help="Skip Splunk forwarding")
    args = parser.parse_args()

    if not args.list and not args.dry_run and os.geteuid() != 0:
        print("[!] Run as root (sudo) to ingest samples.")
        sys.exit(1)

    all_samples = get_all_samples()
    print(f"[*] Found {len(all_samples)} samples in theZoo")

    # ── List mode ─────────────────────────────────────────────────────────────

    if args.list:
        print()
        for i, (name, _) in enumerate(all_samples, 1):
            family = map_family(name)
            print(f"  [{i:>3}] {name:<40} → {family}")
        print()
        return

    # ── Select samples ────────────────────────────────────────────────────────

    if args.name:
        selected = [(n, p) for n, p in all_samples if n.lower() == args.name.lower()]
        if not selected:
            print(f"[!] Sample '{args.name}' not found. Use --list to see available samples.")
            sys.exit(1)
    else:
        selected = all_samples[:args.limit]

    # ── Dry run ───────────────────────────────────────────────────────────────

    if args.dry_run:
        print(f"\n[DRY RUN — no ingestion]\n")
        for i, (name, _) in enumerate(selected, 1):
            family = map_family(name)
            print(f"  [{i}] {name} → {family}")
        print()
        return

    # ── Ingest ────────────────────────────────────────────────────────────────

    os.makedirs(TMP_DIR, exist_ok=True)

    success = 0
    failed  = 0

    for i, (name, path) in enumerate(selected, 1):
        family = map_family(name)
        print(f"\n[{i}/{len(selected)}] {name} → {family}")
        ok = ingest_sample(name, path, args.no_splunk)
        if ok:
            success += 1
        else:
            failed += 1

    # Clean up temp dir
    shutil.rmtree(TMP_DIR, ignore_errors=True)

    print(f"\n{'─'*50}")
    print(f"[+] Done — {success} ingested, {failed} failed")
    print(f"    Catalog: sudo python3 /opt/malware-lab/scripts/query.py --stats")
    print()


if __name__ == "__main__":
    main()
