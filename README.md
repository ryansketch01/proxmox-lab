# proxmox-lab Handoff Document

## Project Overview

Building a cybersecurity home lab on Proxmox VE for malware analysis and research.
GitHub repo: https://github.com/ryansketch01/proxmox-lab

---

## Hardware

| Component | Spec |
|---|---|
| **Hypervisor Machine** | HP EliteDesk 800 G3 SFF |
| **CPU** | Intel Core i5-6500 @ 3.20GHz (4 cores) |
| **RAM** | 80GB |
| **Storage** | 1.76TB |
| **Hypervisor** | Proxmox VE 8.x |
| **Main PC** | Windows 11 (Frank) — Splunk host — 192.168.1.54 |
| **Laptop** | Windows 11 — 192.168.1.150 |

---

## Network Layout

- **vmbr0** — Home network bridge (internet access)
- **vmbr1** — Isolated malware network (192.168.100.0/24, no internet)
- **REMnux ens18** — Home network (DHCP, currently 192.168.1.61)
- **REMnux ens19** — Isolated network (192.168.100.1/24 static)
- **FlareVM Ethernet** — Isolated network only (192.168.100.2/24 static)

---

## Virtual Machines

| VM ID | Name | OS | Purpose | Network |
|---|---|---|---|---|
| 100 | REMnux | Ubuntu Noble | Malware analysis + sample repository | vmbr0 + vmbr1 |
| 101 | FlareVM | Windows 10 Pro | Malware detonation & reverse engineering | vmbr1 only |

---

## Snapshots

### REMnux (VM 100)
| Snapshot | Description |
|---|---|
| clean-install | Original OVA import |
| clean-updated | Fully updated |
| network-configured | Both networks configured via netplan |
| inetsim-configured | INetSim + dnsmasq working |
| splunk-integrated | INetSim logs forwarding to Splunk |
| pre-malware-samples | Clean state before first real sample pull |
| malware-repo-configured | ✅ Phase 3 complete — 14 samples ingested, full pipeline working |

### FlareVM (VM 101)
| Snapshot | Description |
|---|---|
| windows-clean | Fresh Windows 10 install |
| flarevm-clean-internet | FlareVM tools installed, vmbr0 still attached |
| flarevm-clean-isolated | ✅ Primary restore point — fully installed, isolated only |
| dns-configured | Static IP set, DNS pointing to REMnux INetSim |

---

## Completed Phases

### Phase 1 — INetSim ✅
- INetSim 1.3.2 installed on REMnux
- dnsmasq installed to handle DNS (INetSim DNS has compatibility bug with Ubuntu Noble)
- dnsmasq config: all DNS queries on ens19 return 192.168.100.1
- INetSim simulates: HTTP(80), HTTPS(443), SMTP(25), SMTPS(465), POP3(110), POP3S(995), FTP(21), FTPS(990)
- FlareVM DNS set to 192.168.100.1 — all domains resolve to REMnux
- Config file: /etc/inetsim/inetsim.conf
- dnsmasq config: /etc/dnsmasq.conf
- Known issue: INetSim DNS fails on Ubuntu Noble — fixed by using dnsmasq instead

### Phase 2 — Splunk Integration ✅
- Splunk Enterprise running on Frank (192.168.1.54)
- New index created: malware-lab
- New HEC token created: malware-lab-hec (token stored in Bitwarden)
- nginx installed on Frank as reverse proxy (Splunk HEC binds to loopback by default on Windows 11)
- nginx config: C:\nginx\nginx\conf\nginx.conf
- nginx proxies 192.168.1.54:8088 → 127.0.0.1:8088
- Windows Firewall rule added for port 8088
- Splunk HEC Global Settings: SSL disabled (required for HTTP forwarding)
- Python forwarder script on REMnux: /tmp/inetsim_forwarder.py
- Script tails /var/log/inetsim/service.log and ships events to Splunk HEC
- Verified: events flowing into malware-lab index in Splunk

### Phase 3 — Malware Sample Repository ✅
- Repository root: /opt/malware-lab/
- Folder structure: samples/{ransomware,trojan,loader,stealer,rat,wiper,dropper,unknown}
- Samples stored as password-protected zips (password: infected — industry standard)
- Catalog stored at: /opt/malware-lab/catalog/catalog.json
- Scripts deployed to: /opt/malware-lab/scripts/
- theZoo cloned to: /opt/theZoo/ (261 samples available)
- MalwareBazaar API key stored in Bitwarden (metadata queries work; file downloads require paid tier)
- Splunk sourcetype: malware:catalog — HEC token: malware-lab-hec
- Splunk dashboard: "Malware Lab" tab added to DefenseClaw Operations Center
- 14 samples ingested as of Phase 3 completion

#### Scripts (scripts/phase3/)
| Script | Purpose |
|---|---|
| setup_repo.sh | One-time setup of /opt/malware-lab/ folder structure |
| ingest.py | Intake a sample: hash, zip, catalog, forward to Splunk |
| query.py | Search catalog by hash, family, tag, date, source |
| thezoo_fetch.py | Bulk ingest from local theZoo clone |
| bazaar_fetch.py | Query MalwareBazaar API (metadata + future downloads) |

#### Key ingest.py config (edit before use)
```python
SPLUNK_HEC_URL   = "http://192.168.1.54:8088/services/collector/event"
SPLUNK_HEC_TOKEN = ""  # malware-lab-hec token from Bitwarden
ZIP_PASS         = "infected"
```

#### Common commands
```bash
# Ingest a single sample
sudo python3 /opt/malware-lab/scripts/ingest.py /tmp/sample.exe --family trojan --source manual

# Pull 10 samples from theZoo
sudo python3 /opt/malware-lab/scripts/thezoo_fetch.py --limit 10

# List all theZoo samples
python3 /opt/malware-lab/scripts/thezoo_fetch.py --list

# Query catalog
python3 /opt/malware-lab/scripts/query.py --stats
python3 /opt/malware-lab/scripts/query.py --family ransomware
python3 /opt/malware-lab/scripts/query.py --sha256 <partial>

# Dry run before ingesting
sudo python3 /opt/malware-lab/scripts/thezoo_fetch.py --limit 5 --dry-run
```

---

## Current Roadmap

| Phase | Description | Status |
|---|---|---|
| Phase 1 | INetSim | ✅ Complete |
| Phase 2 | Splunk Integration | ✅ Complete |
| Phase 3 | Malware Sample Repository | ✅ Complete |
| Phase 4 | Additional VMs | 🔄 In Progress |
| Phase 5 | YARA Rule Development | ⬜ Planned |
| Phase 6 | Threat Detection Training Tool | ⬜ Planned |

---

## Phase 4 — Additional VMs (In Progress)

Planned VM additions in build order:

| VM ID | Name | OS | Purpose | Network | RAM | Storage |
|---|---|---|---|---|---|---|
| 102 | Windows Server | Windows Server 2022 | Realistic attack target for FlareVM detonation | vmbr1 | 8GB | 80GB |
| 103 | Security Onion | Ubuntu | Full packet capture + IDS on vmbr1 traffic | vmbr1 (promiscuous) | 16GB | 200GB |
| 104 | OSINT VM | Kali Linux | Open-source intelligence gathering, feeds Archimedes | vmbr0 only | 8GB | 60GB |
| 105 | Linux Analysis | REMnux/Ubuntu | ELF + Android sample analysis | vmbr0 + vmbr1 | 8GB | 60GB |

**Current status:** Starting with Security Onion (VM 103)

---

## Key File Locations

### REMnux
| File | Purpose |
|---|---|
| /etc/inetsim/inetsim.conf | INetSim configuration |
| /etc/dnsmasq.conf | dnsmasq DNS configuration |
| /etc/netplan/50-cloud-init.yaml | Network configuration |
| /var/log/inetsim/service.log | INetSim service log |
| /var/log/inetsim/report/ | INetSim session reports |
| /tmp/inetsim_forwarder.py | Splunk HEC forwarder script |
| /opt/malware-lab/ | Malware sample repository root |
| /opt/malware-lab/catalog/catalog.json | Master sample catalog |
| /opt/malware-lab/scripts/ | Phase 3 scripts |
| /opt/theZoo/ | theZoo malware sample source |

### Frank (Main PC — 192.168.1.54)
| File | Purpose |
|---|---|
| C:\nginx\nginx\conf\nginx.conf | nginx reverse proxy config |
| C:\Program Files\Splunk\etc\system\local\inputs.conf | Splunk inputs config |
| C:\Program Files\Splunk\etc\apps\splunk_httpinput\local\inputs.conf | Splunk HEC config |

---

## Useful Commands

### Start Lab Session
```bash
# On REMnux — start INetSim
sudo inetsim &

# On REMnux — start log forwarder
sudo python3 /tmp/inetsim_forwarder.py &

# On Frank — start nginx (if not running)
cd C:\nginx\nginx
.\nginx.exe
```

### Stop Lab Session
```bash
# On REMnux
sudo pkill inetsim
sudo pkill -f inetsim_forwarder

# On Frank
cd C:\nginx\nginx
.\nginx.exe -s stop
```

### Revert FlareVM to Clean State
```bash
# In Proxmox shell
qm rollback 101 flarevm-clean-isolated
```

### Splunk Searches
```
index=malware-lab
index=malware-lab sourcetype=inetsim:service
index=malware-lab sourcetype="malware:catalog"
index=malware-lab sourcetype="malware:catalog" | stats count by family
```

### Transfer Files to REMnux (from laptop)
```powershell
scp -o StrictHostKeyChecking=no <file> remnux@192.168.1.61:/tmp/
# Default REMnux password: malware
```

---

## Security Notes

- All credentials and tokens stored in Bitwarden
- No sensitive data committed to GitHub repo
- FlareVM isolated to vmbr1 only — no internet access
- Always revert FlareVM snapshot after each analysis session
- Malware samples stored as password-protected zips (password: infected)
- /opt/malware-lab/samples and /opt/malware-lab/catalog locked to root-only (chmod 700)
- Splunk HEC SSL disabled — only expose port 8088 on LAN, never WAN
- Gitleaks pre-commit hooks active on Archimedes repo

---

## Related Projects

- **Archimedes** — Personal CTI analyst system running on Frank
  - GitHub: https://github.com/ryansketch01/archimedes
  - Uses Splunk Free as data backend
  - Claude Code as runtime agent layer
  - malware-lab Splunk index feeds into Archimedes pipeline
