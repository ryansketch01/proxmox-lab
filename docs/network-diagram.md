# Network Diagram

## Lab Network Architecture

```
Internet
    |
Home Router (192.168.1.1)
    |
    |——————————————————————————————————————
    |                                      |
Main PC (Windows 10)              EliteDesk (Proxmox Host)
192.168.1.X                       192.168.1.X
Browser → Proxmox UI                    |
https://192.168.1.X:8006         ———————————————————
                                 |                   |
                              vmbr0               vmbr1
                         (Home Network)      (Isolated Network)
                         192.168.1.0/24      192.168.100.0/24
                              |                   |
                         ———————————         ——————————————
                         |         |         |            |
                      REMnux    (future)  REMnux       FlareVM
                      ens18               ens19        Ethernet
                   192.168.1.61        192.168.100.1  192.168.100.X
```

---

## Network Interfaces

### Proxmox Host Bridges

| Bridge | Type | Network | Purpose |
|---|---|---|---|
| vmbr0 | Linux Bridge | 192.168.1.0/24 | Home network, internet access |
| vmbr1 | Linux Bridge | 192.168.100.0/24 | Isolated malware network, no internet |

### REMnux VM

| Interface | Bridge | IP Address | Purpose |
|---|---|---|---|
| ens18 | vmbr0 | 192.168.1.61 (DHCP) | Internet access for tool updates |
| ens19 | vmbr1 | 192.168.100.1/24 (static) | Malware network analysis |

### FlareVM VM

| Interface | Bridge | IP Address | Purpose |
|---|---|---|---|
| Ethernet | vmbr1 | 192.168.100.X (DHCP or static) | Isolated malware detonation |

---

## Security Model

- **FlareVM** has **no internet access** — completely isolated on vmbr1
- **REMnux** is dual-homed — can reach both internet and isolated network
- REMnux acts as the **analysis gateway** between the isolated network and the researcher
- Malware detonated on FlareVM can only communicate on the 192.168.100.0/24 network
- REMnux can capture and analyze all FlareVM network traffic via ens19

---

## Future Network Additions

- **INetSim on REMnux** — simulate internet services (DNS, HTTP, SMTP) for malware that phones home
- **Additional isolated VMs** — more detonation environments on vmbr1
- **Splunk integration** — forward network logs from REMnux to Splunk for analysis
