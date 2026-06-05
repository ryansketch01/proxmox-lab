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
Frank (Windows 11 - Main PC / Splunk Host)
192.168.1.54
  ├── Splunk Enterprise 10.2.2
  │   └── malware-lab index (HEC port 8088)
  └── nginx reverse proxy (192.168.1.54:8088 → 127.0.0.1:8088)

Main PC Browser → https://192.168.1.X:8006 (Proxmox Web UI)

Proxmox Host (EliteDesk - 192.168.1.X)
├── vmbr0 → Home network (internet access)
├── vmbr1 → Isolated malware network (no internet)
├── REMnux VM (100)
│   ├── ens18 → 192.168.1.61 (internet via vmbr0)
│   ├── ens19 → 192.168.100.1 (isolated via vmbr1)
│   ├── INetSim → HTTP/HTTPS/SMTP/FTP simulation
│   ├── dnsmasq → DNS interception (all domains → 192.168.100.1)
│   └── inetsim_forwarder.py → Splunk HEC
└── FlareVM VM (101)
    └── Ethernet → 192.168.100.2 (isolated vmbr1 only)
```

## Virtual Machines

| VM ID | Name | Purpose | Network |
|---|---|---|---|
| 100 | REMnux | Malware analysis workstation | vmbr0 + vmbr1 |
| 101 | FlareVM | Malware detonation & reverse engineering | vmbr1 only |

## Build Roadmap

| Phase | Description | Status |
|---|---|---|
| **Phase 1** | INetSim — Simulate internet services for malware | ✅ Complete |
| **Phase 2** | Splunk Integration — Lab telemetry into Archimedes | ✅ Complete |
| **Phase 3** | Malware Sample Repository — Organized sample storage | 🔄 In Progress |
| **Phase 4** | Additional VMs — Expand lab environment | ⬜ Planned |
| **Phase 5** | YARA Rule Development — Custom detection rules | ⬜ Planned |
| **Phase 6** | Threat Detection Training Tool — Hands-on training platform | ⬜ Planned |

## Documentation

- [Setup Guide](docs/setup-guide.md) — Full step by step build notes
- [Network Diagram](docs/network-diagram.md) — Lab network layout
- [Snapshot Reference](docs/snapshots.md) — Snapshot guide
- [Useful Commands](docs/useful-commands.md) — Handy command reference
- [INetSim Setup](docs/inetsim-setup.md) — INetSim and dnsmasq configuration
- [Splunk Integration](docs/splunk-integration.md) — HEC forwarding and nginx proxy

## Splunk

- **Host:** Frank (192.168.1.54)
- **Version:** Splunk Enterprise 10.2.2
- **Index:** malware-lab
- **HEC Token:** stored in Bitwarden
- **Search:** `index=malware-lab`

## Security Notes

- FlareVM is **isolated network only** — no direct internet access
- REMnux is dual-homed — analysis gateway between isolated network and researcher
- Splunk HEC token stored in Bitwarden — never commit tokens to repo
- nginx proxy binds only to home network interface (192.168.1.54)
- Always revert FlareVM to `flarevm-clean-isolated` snapshot after each analysis session
- Malware samples should never be run outside of the isolated vmbr1 network
