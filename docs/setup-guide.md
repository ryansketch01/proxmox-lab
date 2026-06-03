# Setup Guide

Complete step by step guide for building the proxmox-lab from scratch.

---

## Prerequisites

- HP EliteDesk 800 G3 SFF (or equivalent hardware)
- USB drive (2GB minimum)
- Ethernet cable (wired connection strongly recommended)
- Windows PC for management

---

## Phase 1 — Proxmox VE Installation

### Step 1 — Download Proxmox ISO
- Go to https://proxmox.com/en/downloads
- Download the latest Proxmox VE ISO (8.x)

### Step 2 — Flash USB with Rufus
- Download Rufus from https://rufus.ie
- Insert USB drive
- Select the Proxmox ISO
- When prompted select **DD Image mode** (Proxmox ISOs are ISOHybrid format)
- Click Start and wait for completion

### Step 3 — Boot EliteDesk from USB
- Connect ethernet cable to EliteDesk and router
- Insert USB drive into EliteDesk
- Power on and tap **F9** repeatedly to open boot menu
- Select USB drive from boot menu

### Step 4 — Proxmox Installer
- Select **Install Proxmox VE (Graphical)**
- Accept license agreement
- Select target hard disk
- Set location and timezone
- Set root password and email
- Network configuration:
  - Management Interface: ethernet port (not WiFi)
  - Hostname: `pve.home.lab`
  - IP Address: assigned by router (note this down)
  - Gateway: router IP
  - DNS: router IP
- Click Install and wait (~5-10 minutes)
- Remove USB after reboot

### Step 5 — Access Proxmox Web UI
- On your main PC open a browser
- Navigate to `https://192.168.1.X:8006` (use IP noted during install)
- Accept the self-signed certificate warning
- Login: username `root`, password set during install
- Dismiss the "No Valid Subscription" popup (normal for free version)

---

## Phase 2 — REMnux VM Setup

### Step 1 — Download REMnux OVA
- Go to https://remnux.org
- Download the Virtual Appliance OVA file (~4-5GB)

### Step 2 — Upload to Proxmox
- In Proxmox web UI click **local (pve)** → **Import**
- Click **Upload** and select the REMnux OVA file

### Step 3 — Extract the OVA
```bash
tar -xvf /var/lib/vz/import/remnux-noble-amd64.ova -C /var/lib/vz/import/
```

### Step 4 — Decompress the VMDK
```bash
gunzip /var/lib/vz/import/remnux-noble-amd64-disk1.vmdk.gz
```

### Step 5 — Create the VM
```bash
qm create 100 --name remnux --memory 8192 --cores 2 --net0 virtio,bridge=vmbr0 --ostype other
```

### Step 6 — Import the Disk
```bash
qm importdisk 100 /var/lib/vz/import/remnux-noble-amd64-disk1.vmdk local-lvm
```

### Step 7 — Configure the VM
```bash
qm set 100 --scsihw virtio-scsi-pci --scsi0 local-lvm:vm-100-disk-0
qm set 100 --boot c --bootdisk scsi0
qm set 100 --vga std
qm set 100 --ide2 local-lvm:cloudinit
```

### Step 8 — Start REMnux
```bash
qm start 100
```

### Step 9 — Update REMnux
```bash
sudo apt-get update && sudo apt-get upgrade -y
```

---

## Phase 3 — Network Isolation Setup

### Step 1 — Create Isolated Network Bridge
- In Proxmox web UI click **pve** → **Network**
- Click **Create** → **Linux Bridge**
- Name: `vmbr1`
- Leave IP blank
- Comment: `Isolated malware network`
- Check Autostart
- Click **Apply Configuration**

### Step 2 — Add Second NIC to REMnux
- Click **100 (remnux)** → **Hardware** → **Add** → **Network Device**
- Bridge: `vmbr1`
- Model: VirtIO
- Restart REMnux

### Step 3 — Configure REMnux Networking
Edit `/etc/netplan/50-cloud-init.yaml`:
```yaml
network:
  version: 2
  ethernets:
    ens18:
      dhcp4: true
    ens19:
      dhcp4: no
      addresses:
        - 192.168.100.1/24
```

Apply configuration:
```bash
sudo netplan apply
```

---

## Phase 4 — FlareVM Setup

### Step 1 — Download Windows 10 ISO
- Go to https://www.microsoft.com/en-us/software-download/windows10
- Download the ISO using the media creation tool
- Select 64-bit ISO format

### Step 2 — Upload Windows 10 ISO to Proxmox
- In Proxmox web UI click **local (pve)** → **ISO Images** → **Upload**

### Step 3 — Download VirtIO Drivers
```bash
wget https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso -O /var/lib/vz/template/iso/virtio-win.iso
```

### Step 4 — Create FlareVM VM
- Click **Create VM** in Proxmox web UI
- General: ID `101`, Name `flarevm`
- OS: Windows 10 ISO, Type Microsoft Windows
- System: q35, OVMF (UEFI), EFI storage: local-lvm, TPM: local-lvm v2.0
- Disks: 100GB on local-lvm
- CPU: 2 cores
- Memory: 8192MB
- Network: **vmbr1 only** (isolated)

### Step 5 — Install Windows 10
- Start VM and boot from ISO
- Select Windows 10 Pro
- Custom install to unallocated drive
- Skip network setup (select "I don't have internet")
- Username: `flarevm`
- Turn all privacy settings Off

### Step 6 — Install VirtIO Network Drivers
- Attach virtio-win.iso as second CD drive in Hardware
- In Windows File Explorer open VirtIO drive
- Navigate to `NetKVM\w10\amd64`
- Right click `netkvm.inf` → Install
- Also run `virtio-win-guest-tools.exe` from root of VirtIO drive

### Step 7 — Temporarily Add Internet for FlareVM Installer
- Add vmbr0 network adapter in Proxmox Hardware
- In Windows configure the new adapter via NetworkManager

### Step 8 — Install FlareVM Toolset
- Disable Windows Defender via Group Policy:
  `gpedit.msc` → Computer Configuration → Administrative Templates → Windows Components → Microsoft Defender Antivirus → Turn off → Enabled
- Reboot
- Open PowerShell as Administrator:
```powershell
Set-ExecutionPolicy Unrestricted -Force
(New-Object Net.WebClient).DownloadFile('https://raw.githubusercontent.com/mandiant/flare-vm/main/install.ps1','install.ps1')
Unblock-File .\install.ps1
.\install.ps1
```
- Accept defaults in package selection
- Wait 1-3 hours for installation to complete

### Step 9 — Remove Internet Access
- In Proxmox Hardware remove the vmbr0 network adapter
- FlareVM is now isolated to vmbr1 only
