#!/usr/bin/env python3
"""
bazaar_fetch.py — MalwareBazaar Sample Fetcher
Phase 3, proxmox-lab

Pulls recent malware samples from MalwareBazaar (bazaar.abuse.ch),
downloads them, and passes each through ingest.py automatically.

Usage:
    sudo python3 bazaar_fetch.py [options]

Options:
    --limit     Number of recent samples to fetch (default: 10, max: 100)
    --family    Filter by malware family name (e.g. LockBit, AgentTesla)
    --tag       Filter by tag (e.g. exe, doc, emotet)
    --dry-run   Query and list samples without downloading
    --no-splunk Skip Splunk forwarding during ingest

Examples:
    sudo python3 bazaar_fetch.py --limit 5
    sudo python3 bazaar_fetch.py --limit 10 --family AgentTesla
    sudo python3 bazaar_fetch.py --limit 20 --dry-run
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────

BAZAAR_API_URL  = "https://mb-api.abuse.ch/api/v1/"
DOWNLOAD_URL    = "https://mb-api.abuse.ch/api/v1/"
SCRIPTS_DIR     = "/opt/malware-lab/scripts"
INGEST_SCRIPT   = os.path.join(SCRIPTS_DIR, "ingest.py")
TMP_DIR         = "/tmp/bazaar_fetch"

# MalwareBazaar family → our local family taxonomy
FAMILY_MAP = {
    "ransomware": "ransomware",
    "lockbit":    "ransomware",
    "blackcat":   "ransomware",
    "revil":      "ransomware",
    "wannacry":   "ransomware",
    "agenttesla": "stealer",
    "redline":    "stealer",
    "raccoon":    "stealer",
    "vidar":      "stealer",
    "formbook":   "stealer",
    "remcos":     "rat",
    "asyncrat":   "rat",
    "nanocore":   "rat",
    "njrat":      "rat",
    "emotet":     "loader",
    "qakbot":     "loader",
    "icedid":     "loader",
    "bumblebee":  "loader",
    "cobalt":     "loader",
    "cobaltstrike": "loader",
    "metasploit": "trojan",
    "mirai":      "trojan",
    "dridex":     "trojan",
    "trickbot":   "trojan",
    "hermetic":   "wiper",
    "whispergate":"wiper",
}

def map_family(bazaar_family: str) -> str:
    """Map MalwareBazaar family name to our local taxonomy."""
    if not bazaar_family:
        return "unknown"
    key = bazaar_family.lower().replace(" ", "")
    for pattern, local in FAMILY_MAP.items():
        if pattern in key:
            return local
    return "unknown"

# ── API ───────────────────────────────────────────────────────────────────────

def query_recent(limit: int) -> list:
    """Query MalwareBazaar for recent samples."""
    print(f"[*] Querying MalwareBazaar for {limit} recent samples...")
    payload = urllib.parse.urlencode({
        "query": "get_recent",
        "selector": str(min(limit, 100))
    }).encode("utf-8")

    req = urllib.request.Request(
        BAZAAR_API_URL,
        data=payload,
        headers={"Auth-Key": BAZAAR_API_KEY, "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())

    if data.get("query_status") != "ok":
        print(f"[!] MalwareBazaar API error: {data.get('query_status')}")
        sys.exit(1)

    return data.get("data", [])

def query_by_family(family: str, limit: int) -> list:
    """Query MalwareBazaar by malware family."""
    print(f"[*] Querying MalwareBazaar for family '{family}' (limit {limit})...")
    payload = urllib.parse.urlencode({
        "query": "get_signame",
        "signature": family,
        "limit": str(min(limit, 100))
    }).encode("utf-8")

    req = urllib.request.Request(
        BAZAAR_API_URL,
        data=payload,
        headers={"Auth-Key": BAZAAR_API_KEY, "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())

    if data.get("query_status") not in ("ok", "no_results"):
        print(f"[!] MalwareBazaar API error: {data.get('query_status')}")
        sys.exit(1)

    return data.get("data", [])

def query_by_tag(tag: str, limit: int) -> list:
    """Query MalwareBazaar by tag."""
    print(f"[*] Querying MalwareBazaar for tag '{tag}' (limit {limit})...")
    payload = urllib.parse.urlencode({
        "query": "get_taginfo",
        "tag": tag,
        "limit": str(min(limit, 100))
    }).encode("utf-8")

    req = urllib.request.Request(
        BAZAAR_API_URL,
        data=payload,
        headers={"Auth-Key": BAZAAR_API_KEY, "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())

    if data.get("query_status") not in ("ok", "no_results"):
        print(f"[!] MalwareBazaar API error: {data.get('query_status')}")
        sys.exit(1)

    return data.get("data", [])

# ── Download ──────────────────────────────────────────────────────────────────

def download_sample(sha256: str, dest_dir: str) -> str | None:
    """
    Download a sample from MalwareBazaar by SHA256.
    Returns path to downloaded zip file, or None on failure.
    MalwareBazaar delivers samples as password-protected zips (password: infected).
    """
    payload = urllib.parse.urlencode({
        "query": "get_file",
        "sha256_hash": sha256,
    }).encode("utf-8")

    req = urllib.request.Request(
        BAZAAR_API_URL,
        data=payload,
        headers={"Auth-Key": BAZAAR_API_KEY, "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    dest_path = os.path.join(dest_dir, f"{sha256}.zip")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            content_type = resp.headers.get("Content-Type", "")
            if "application/json" in content_type:
                try:
                    error = json.loads(raw.decode())
                    print(f"  [!] Download error: {error.get('query_status', 'unknown')}")
                except Exception:
                    print(f"  [!] Download error: unexpected response")
                return None

            with open(dest_path, "wb") as f:
                f.write(raw)

        return dest_path

    except urllib.error.URLError as e:
        print(f"  [!] Download failed: {e}")
        return None

# ── Unzip + Ingest ────────────────────────────────────────────────────────────

def unzip_and_ingest(zip_path: str, sha256: str, sample: dict, no_splunk: bool) -> bool:
    """
    Unzip the MalwareBazaar archive (password: infected),
    extract the raw sample, then pass it to ingest.py.
    """
    extract_dir = os.path.join(TMP_DIR, sha256)
    os.makedirs(extract_dir, exist_ok=True)

    # Unzip with password
    result = subprocess.run(
        ["unzip", "-P", "infected", "-o", zip_path, "-d", extract_dir],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"  [!] Unzip failed: {result.stderr.strip()}")
        return False

    # Find extracted file (exclude __MACOSX artifacts)
    extracted = [
        os.path.join(extract_dir, f)
        for f in os.listdir(extract_dir)
        if not f.startswith(".")
    ]

    if not extracted:
        print(f"  [!] No files found after unzip")
        return False

    raw_sample = extracted[0]

    # Build ingest.py arguments
    family   = map_family(sample.get("signature", ""))
    source   = "MalwareBazaar"
    tags     = sample.get("tags") or []
    if sample.get("signature"):
        tags.insert(0, sample["signature"])
    tags_str = ",".join(tags)
    notes    = f"File type: {sample.get('file_type', 'unknown')} | " \
               f"First seen: {sample.get('first_seen', 'unknown')}"

    cmd = [
        "python3", INGEST_SCRIPT,
        raw_sample,
        "--family", family,
        "--source", source,
        "--tags",   tags_str,
        "--notes",  notes,
    ]
    if no_splunk:
        cmd.append("--no-splunk")

    result = subprocess.run(cmd, capture_output=False, text=True)
    return result.returncode == 0

# ── Display (dry run) ─────────────────────────────────────────────────────────

def print_sample_info(i: int, sample: dict) -> None:
    print(f"\n  [{i}] {sample.get('signature', 'Unknown')} — {sample.get('file_type', '?')}")
    print(f"       SHA256     : {sample.get('sha256_hash', 'N/A')}")
    print(f"       First seen : {sample.get('first_seen', 'N/A')}")
    print(f"       Tags       : {', '.join(sample.get('tags') or []) or 'none'}")
    print(f"       Reporter   : {sample.get('reporter', 'N/A')}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Fetch malware samples from MalwareBazaar.")
    parser.add_argument("--limit",     type=int, default=10, help="Number of samples (default: 10)")
    parser.add_argument("--family",    default="",           help="Filter by malware family")
    parser.add_argument("--tag",       default="",           help="Filter by tag")
    parser.add_argument("--dry-run",   action="store_true",  help="List without downloading")
    parser.add_argument("--no-splunk", action="store_true",  help="Skip Splunk forwarding")
    args = parser.parse_args()

    if not args.dry_run and os.geteuid() != 0:
        print("[!] Run as root (sudo) for downloading and ingesting samples.")
        sys.exit(1)

    # ── Query ─────────────────────────────────────────────────────────────────

    try:
        if args.family:
            samples = query_by_family(args.family, args.limit)
        elif args.tag:
            samples = query_by_tag(args.tag, args.limit)
        else:
            samples = query_recent(args.limit)
    except urllib.error.URLError as e:
        print(f"[!] Could not reach MalwareBazaar: {e}")
        sys.exit(1)

    if not samples:
        print("[!] No samples returned.")
        sys.exit(0)

    print(f"[+] Got {len(samples)} sample(s) from MalwareBazaar")

    # ── Dry run ───────────────────────────────────────────────────────────────

    if args.dry_run:
        print("\n[DRY RUN — no downloads]")
        for i, sample in enumerate(samples, 1):
            print_sample_info(i, sample)
        print()
        return

    # ── Download + Ingest ─────────────────────────────────────────────────────

    os.makedirs(TMP_DIR, exist_ok=True)

    success = 0
    failed  = 0

    for i, sample in enumerate(samples, 1):
        sha256 = sample.get("sha256_hash", "")
        sig    = sample.get("signature", "Unknown")
        print(f"\n[{i}/{len(samples)}] {sig} ({sha256[:16]}...)")

        zip_path = download_sample(sha256, TMP_DIR)
        if not zip_path:
            failed += 1
            continue

        print(f"  [*] Downloaded — ingesting...")
        ok = unzip_and_ingest(zip_path, sha256, sample, args.no_splunk)

        # Clean up temp zip and extract dir
        try:
            os.remove(zip_path)
            extract_dir = os.path.join(TMP_DIR, sha256)
            if os.path.isdir(extract_dir):
                import shutil
                shutil.rmtree(extract_dir)
        except Exception:
            pass

        if ok:
            success += 1
        else:
            failed += 1

    # ── Summary ───────────────────────────────────────────────────────────────

    print(f"\n{'─'*50}")
    print(f"[+] Done — {success} ingested, {failed} failed")
    print(f"    Catalog: sudo python3 {SCRIPTS_DIR}/query.py --stats")
    print()


if __name__ == "__main__":
    main()
