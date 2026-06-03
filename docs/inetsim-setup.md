# INetSim Setup Guide

INetSim simulates internet services (HTTP, HTTPS, SMTP, FTP, DNS) on the isolated network so malware thinks it has internet access while remaining completely contained.

---

## Architecture

```
FlareVM (malware detonation)
    ↓ DNS query: "where is google.com?"
dnsmasq on REMnux (192.168.100.1)
    ↓ answers: "192.168.100.1"
INetSim on REMnux
    ↓ simulates HTTP/HTTPS/SMTP/FTP/etc.
Researcher captures and analyzes all traffic
```

---

## Installation

### Step 1 — Install INetSim
```bash
sudo apt-get update
sudo apt-get install inetsim -y
```

### Step 2 — Install dnsmasq (required for DNS)
INetSim 1.3.2 has a known DNS compatibility issue with Ubuntu Noble (24.04).
dnsmasq is used instead to handle DNS interception.

```bash
sudo apt-get install dnsmasq -y
```

---

## Configuration

### INetSim Configuration
Edit `/etc/inetsim/inetsim.conf`:

```bash
sudo nano /etc/inetsim/inetsim.conf
```

Key settings to change:
```
service_bind_address    192.168.100.1
dns_default_ip          192.168.100.1
```

Also uncomment:
```
start_service dns
dns_bind_port    53
```

### Fix systemd-resolved DNS Conflict
Ubuntu uses systemd-resolved which occupies port 53. Disable its stub listener:

```bash
sudo nano /etc/systemd/resolved.conf
```

Change:
```
DNSStubListener=no
```

Restart:
```bash
sudo systemctl restart systemd-resolved
```

### dnsmasq Configuration
Edit `/etc/dnsmasq.conf`:

```bash
sudo nano /etc/dnsmasq.conf
```

Add these lines:
```
interface=ens19
address=/#/192.168.100.1
listen-address=192.168.100.1
bind-interfaces
no-resolv
```

This makes dnsmasq:
- Listen only on the isolated interface (ens19)
- Return 192.168.100.1 for ALL DNS queries
- Not use any upstream DNS servers

Start and enable dnsmasq:
```bash
sudo systemctl start dnsmasq
sudo systemctl enable dnsmasq
```

---

## Starting INetSim

Run INetSim in the background:
```bash
sudo inetsim &
```

Services that start successfully:
```
http      80   ✅
https     443  ✅
ftp       21   ✅
smtp      25   ✅
smtps     465  ✅
pop3      110  ✅
pop3s     995  ✅
ftps      990  ✅
dns       53   ✅ (handled by dnsmasq)
```

---

## FlareVM Configuration

Assign a static IP to FlareVM on the isolated network:

```powershell
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 192.168.100.2 -PrefixLength 24 -DefaultGateway 192.168.100.1
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses 192.168.100.1
```

---

## Verification

Test DNS interception from FlareVM:
```powershell
nslookup google.com 192.168.100.1
```

Expected result:
```
Server:   192.168.100.1
Address:  192.168.100.1

Name:     google.com
Address:  192.168.100.1
```

Any domain resolves to 192.168.100.1 — all malware traffic is redirected to REMnux.

---

## Stopping INetSim

```bash
sudo pkill inetsim
```

---

## INetSim Logs

Logs are stored in `/var/log/inetsim/`:
```bash
# View main log
sudo cat /var/log/inetsim/main.log

# View service interaction log
sudo cat /var/log/inetsim/service.log

# View reports
ls /var/log/inetsim/report/
```

Reports show every connection malware made during the analysis session.

---

## Known Issues

### INetSim DNS fails on Ubuntu Noble (24.04)
INetSim 1.3.2 uses a deprecated Net::DNS method that fails on newer Ubuntu versions.
**Solution:** Use dnsmasq for DNS as described above.

### systemd-resolved occupies port 53
**Solution:** Set `DNSStubListener=no` in `/etc/systemd/resolved.conf`
