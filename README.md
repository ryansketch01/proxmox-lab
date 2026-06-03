# proxmox-lab

A cybersecurity home lab built on Proxmox VE for malware analysis and research.

## Overview

This repo documents the setup and configuration of a personal cybersecurity home lab running on an HP EliteDesk 800 G3 SFF. The lab is purpose-built for malware analysis and reverse engineering research.

## Hardware

| Component | Spec |
|---|---|
| **Machine** | HP EliteDesk 800 G3 SFF |
| **CPU** | Intel Core i5-6500 @ 3.20GHz (4 cores) |
| **RAM** | 80GB |
| **Storage** | 1.76TB |
| **Hypervisor** | Proxmox VE 8.x |

## Lab Architecture

```
Your Main PC (Windows 10)
  └── Browser → https://192.168.1.X:8006 (Proxmox Web UI)

Proxmox Host (EliteDesk)
├── vmbr0 → Home network (internet access)
├── vmbr1 → Isolated malware network (no internet)
├── REMnux VM
│   ├── ens18 → 192.168.1.61 (internet via vmbr0)
│   └── ens19 → 192.168.100.1 (isolated via vmbr1)
└── FlareVM VM
    └── Ethernet → vmbr1 (isolated only)
```

## Virtual Machines

| VM ID | Name | Purpose | Network |
|---|---|---|---|
| 100 | REMnux | Malware analysis workstation | vmbr0 + vmbr1 |
| 101 | FlareVM | Malware detonation & reverse engineering | vmbr1 only |

## Documentation

- [Setup Guide](docs/setup-guide.md) — Full step by step build notes
- [Network Diagram](docs/network-diagram.md) — Lab network layout
- [Snapshot Reference](docs/snapshots.md) — Snapshot guide
- [Useful Commands](docs/useful-commands.md) — Handy command reference

## Security Notes

- FlareVM is **isolated network only** — no direct internet access
- REMnux has dual-homed networking for analysis of isolated VM traffic
- Always revert FlareVM to `flarevm-clean-isolated` snapshot after each analysis session
- Malware samples should never be run outside of the isolated vmbr1 network
