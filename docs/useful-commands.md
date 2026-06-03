# Useful Commands

A reference of handy commands for managing the proxmox-lab.

---

## Proxmox Shell Commands

### VM Management
```bash
# List all VMs
qm list

# Start a VM
qm start <vmid>

# Stop a VM
qm stop <vmid>

# Shutdown a VM gracefully
qm shutdown <vmid>

# Reboot a VM
qm reboot <vmid>

# Check VM status
qm status <vmid>
```

### Snapshot Management
```bash
# List snapshots for a VM
qm listsnapshot <vmid>

# Take a snapshot
qm snapshot <vmid> <snapshot-name> --description "<description>"

# Revert to a snapshot
qm rollback <vmid> <snapshot-name>

# Delete a snapshot
qm delsnapshot <vmid> <snapshot-name>
```

### Storage
```bash
# List storage contents
pvesm list local
pvesm list local-lvm

# Check disk usage
df -h
```

### Network
```bash
# Show network interfaces on Proxmox host
ip addr show

# Restart networking
systemctl restart networking
```

---

## REMnux Commands

### Network
```bash
# Check network interfaces
ip addr show

# Apply netplan configuration
sudo netplan apply

# Test internet connectivity
ping 8.8.8.8

# Capture traffic on isolated interface
sudo tcpdump -i ens19 -w /tmp/capture.pcap
```

### Malware Analysis Tools
```bash
# Analyze file with YARA rules
yara /path/to/rules.yar /path/to/sample

# Static analysis with strings
strings /path/to/sample

# Check file type
file /path/to/sample

# Calculate hashes
md5sum /path/to/sample
sha256sum /path/to/sample

# Analyze PE file
pescanner /path/to/sample

# Run CAPA capabilities analysis
capa /path/to/sample
```

### Network Simulation (INetSim)
```bash
# Start INetSim (simulates internet services for isolated VMs)
sudo inetsim

# Stop INetSim
sudo inetsim --stop
```

---

## FlareVM Commands (PowerShell)

### General
```powershell
# Check network interfaces
ipconfig /all

# Test connectivity to REMnux
ping 192.168.100.1

# List running processes
Get-Process

# List network connections
netstat -ano
```

### Analysis
```powershell
# Calculate file hash
Get-FileHash -Algorithm SHA256 /path/to/sample

# Check file signature
Get-AuthenticodeSignature /path/to/sample
```

---

## Proxmox Web UI Quick Reference

| Action | Location |
|---|---|
| Create VM | Top right **Create VM** button |
| Upload ISO | local (pve) → ISO Images → Upload |
| Take snapshot | VM → Snapshots → Take Snapshot |
| Revert snapshot | VM → Snapshots → select → Rollback |
| Add network adapter | VM → Hardware → Add → Network Device |
| Open VM console | VM → Console |
| Open Proxmox shell | pve → Shell |
| View network bridges | pve → Network |
