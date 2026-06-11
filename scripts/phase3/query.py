#!/usr/bin/env python3
"""
query.py — Malware Sample Catalog Query Tool
Phase 3, proxmox-lab

Usage:
    python3 query.py [options]

Options:
    --sha256    Search by SHA256 hash (partial match supported)
    --md5       Search by MD5 hash (partial match supported)
    --sha1      Search by SHA1 hash (partial match supported)
    --family    Filter by malware family (e.g. ransomware, trojan)
    --source    Filter by source (e.g. MalwareBazaar, manual)
    --tags      Filter by tag (single tag, e.g. LockBit)
    --date      Filter by ingest date (YYYY-MM-DD)
    --since     Filter samples ingested on or after date (YYYY-MM-DD)
    --notes     Search notes field (partial match)
    --list-all  List all samples in catalog
    --stats     Show catalog statistics
    --json      Output results as raw JSON

Examples:
    python3 query.py --list-all
    python3 query.py --family ransomware
    python3 query.py --tags LockBit
    python3 query.py --sha256 abc123
    python3 query.py --since 2026-06-01 --family trojan
    python3 query.py --stats
"""

import argparse
import json
import os
import sys
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────

REPO_ROOT = "/opt/malware-lab"
CATALOG   = os.path.join(REPO_ROOT, "catalog", "catalog.json")

FAMILY_COLORS = {
    "ransomware": "\033[91m",   # red
    "trojan":     "\033[93m",   # yellow
    "loader":     "\033[95m",   # magenta
    "stealer":    "\033[96m",   # cyan
    "rat":        "\033[94m",   # blue
    "wiper":      "\033[91m",   # red
    "dropper":    "\033[95m",   # magenta
    "unknown":    "\033[90m",   # grey
}
RESET = "\033[0m"
BOLD  = "\033[1m"

# ── Catalog ───────────────────────────────────────────────────────────────────

def load_catalog() -> list:
    if not os.path.exists(CATALOG):
        print(f"[!] Catalog not found at {CATALOG}")
        sys.exit(1)
    with open(CATALOG, "r") as f:
        return json.load(f)

# ── Filtering ─────────────────────────────────────────────────────────────────

def filter_catalog(catalog: list, args) -> list:
    results = catalog

    if args.sha256:
        results = [r for r in results if args.sha256.lower() in r["sha256"].lower()]
    if args.md5:
        results = [r for r in results if args.md5.lower() in r["md5"].lower()]
    if args.sha1:
        results = [r for r in results if args.sha1.lower() in r["sha1"].lower()]
    if args.family:
        results = [r for r in results if r["family"].lower() == args.family.lower()]
    if args.source:
        results = [r for r in results if args.source.lower() in r["source"].lower()]
    if args.tags:
        results = [r for r in results if any(
            args.tags.lower() in t.lower() for t in r.get("tags", [])
        )]
    if args.date:
        results = [r for r in results if r["date_ingested"] == args.date]
    if args.since:
        results = [r for r in results if r["date_ingested"] >= args.since]
    if args.notes:
        results = [r for r in results if args.notes.lower() in r.get("notes", "").lower()]

    return results

# ── Display ───────────────────────────────────────────────────────────────────

def print_record(r: dict, index: int) -> None:
    family = r.get("family", "unknown")
    color  = FAMILY_COLORS.get(family, "")

    print(f"\n{BOLD}[{index}]{RESET} {color}{family.upper()}{RESET}")
    print(f"  SHA256   : {r['sha256']}")
    print(f"  MD5      : {r['md5']}")
    print(f"  SHA1     : {r['sha1']}")
    print(f"  Filename : {r.get('filename_original', 'N/A')}")
    print(f"  Source   : {r.get('source', 'N/A')}")
    print(f"  Ingested : {r.get('date_ingested', 'N/A')}")
    print(f"  Tags     : {', '.join(r.get('tags', [])) or 'none'}")
    print(f"  IOCs     : {', '.join(r.get('iocs', [])) or 'none'}")
    print(f"  Zip      : {r.get('zip_path', 'N/A')}")
    if r.get("notes"):
        print(f"  Notes    : {r['notes']}")

def print_stats(catalog: list) -> None:
    if not catalog:
        print("Catalog is empty.")
        return

    from collections import Counter
    families = Counter(r["family"] for r in catalog)
    sources  = Counter(r["source"] for r in catalog)
    dates    = sorted(set(r["date_ingested"] for r in catalog))

    print(f"\n{BOLD}Catalog Statistics{RESET}")
    print(f"  Total samples : {len(catalog)}")
    print(f"\n  By family:")
    for family, count in families.most_common():
        color = FAMILY_COLORS.get(family, "")
        print(f"    {color}{family:<12}{RESET} {count}")
    print(f"\n  By source:")
    for source, count in sources.most_common():
        print(f"    {source:<20} {count}")
    print(f"\n  Date range    : {dates[0]} → {dates[-1]}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Query the malware sample catalog.")
    parser.add_argument("--sha256",   default="", help="Search by SHA256 (partial)")
    parser.add_argument("--md5",      default="", help="Search by MD5 (partial)")
    parser.add_argument("--sha1",     default="", help="Search by SHA1 (partial)")
    parser.add_argument("--family",   default="", help="Filter by family")
    parser.add_argument("--source",   default="", help="Filter by source")
    parser.add_argument("--tags",     default="", help="Filter by tag")
    parser.add_argument("--date",     default="", help="Filter by exact date (YYYY-MM-DD)")
    parser.add_argument("--since",    default="", help="Filter since date (YYYY-MM-DD)")
    parser.add_argument("--notes",    default="", help="Search notes field")
    parser.add_argument("--list-all", action="store_true", help="List all samples")
    parser.add_argument("--stats",    action="store_true", help="Show catalog statistics")
    parser.add_argument("--json",     action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    catalog = load_catalog()

    # Stats mode
    if args.stats:
        print_stats(catalog)
        return

    # List all or filter
    if args.list_all:
        results = catalog
    else:
        results = filter_catalog(catalog, args)

    if not results:
        print("No samples matched your query.")
        return

    # Output
    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"\n{BOLD}Found {len(results)} sample(s):{RESET}")
    for i, record in enumerate(results, 1):
        print_record(record, i)
    print()


if __name__ == "__main__":
    main()
