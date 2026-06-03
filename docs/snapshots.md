# Snapshot Reference

## Overview

Snapshots are the foundation of a safe malware analysis lab. Always revert to a clean snapshot after each analysis session.

---

## REMnux Snapshots (VM 100)

| Snapshot Name | Description | When Created |
|---|---|---|
| `clean-install` | REMnux immediately after OVA import | After initial import |
| `clean-updated` | REMnux fully updated, no other changes | After first apt-get upgrade |
| `network-configured` | Both ens18 and ens19 configured via netplan | After network setup |

---

## FlareVM Snapshots (VM 101)

| Snapshot Name | Description | When Created |
|---|---|---|
| `windows-clean` | Fresh Windows 10 install, no activation | After Windows 10 setup |
| `flarevm-clean-internet` | FlareVM tools installed, vmbr0 still attached | After FlareVM install, before cleanup |
| `flarevm-clean-isolated` | ✅ **Primary restore point** — FlareVM fully installed, isolated network only | After removing vmbr0 adapter |

---

## How to Revert a Snapshot

### Via Proxmox Web UI
1. Click on the VM in the left panel
2. Click **Snapshots**
3. Select the snapshot to revert to
4. Click **Rollback**
5. Confirm

### Via Proxmox Shell
```bash
qm rollback <vmid> <snapshot-name>

# Examples:
qm rollback 101 flarevm-clean-isolated
qm rollback 100 network-configured
```

---

## Snapshot Best Practices

- **Always snapshot before** installing new tools or making configuration changes
- **Always revert** FlareVM to `flarevm-clean-isolated` after each malware analysis session
- **Name snapshots descriptively** — include date for time-sensitive snapshots
- **Don't accumulate too many snapshots** — they consume disk space; delete old ones periodically

---

## Taking a New Snapshot

### Via Proxmox Web UI
1. Click on the VM in the left panel
2. Click **Snapshots**
3. Click **Take Snapshot**
4. Enter a name and description
5. Click **Take Snapshot**

### Via Proxmox Shell
```bash
qm snapshot <vmid> <snapshot-name> --description "<description>"

# Example:
qm snapshot 101 flarevm-clean-isolated --description "FlareVM fully installed, isolated network only"
```
