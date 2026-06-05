# Splunk Integration Guide

This documents the integration between the malware lab and Splunk for log forwarding and analysis.

---

## Architecture

```
FlareVM (malware activity)
    ↓
INetSim on REMnux (intercepts traffic)
    ↓
inetsim_forwarder.py (tails service.log)
    ↓
nginx proxy (192.168.1.54:8088)
    ↓
Splunk HEC (malware-lab index)
    ↓
Archimedes CTI pipeline
```

---

## Splunk Configuration

### New Index
- **Name:** malware-lab
- **Type:** Events

### New HEC Token
- **Name:** malware-lab-hec
- **Index:** malware-lab
- **Token:** stored securely in Bitwarden

### Receiving Port
- Port 9997 configured but inactive (replaced by HEC)

---

## nginx Reverse Proxy Setup

Splunk HEC on Windows 11 binds to loopback (127.0.0.1) by default.
nginx is used as a reverse proxy to expose HEC to the home network securely.

### Installation
- Download nginx for Windows from https://nginx.org/en/download.html
- Extract to `C:\nginx\nginx\`

### Configuration
Edit `C:\nginx\nginx\conf\nginx.conf`:

```nginx
worker_processes 1;

events {
    worker_connections 1024;
}

stream {
    server {
        listen 192.168.1.54:8088;
        proxy_pass 127.0.0.1:8088;
    }
}
```

### Starting nginx
```powershell
cd C:\nginx\nginx
.\nginx.exe
```

### Stopping nginx
```powershell
cd C:\nginx\nginx
.\nginx.exe -s stop
```

### Make nginx Start Automatically
To run nginx as a Windows service use NSSM (Non-Sucking Service Manager):
```powershell
nssm install nginx C:\nginx\nginx\nginx.exe
nssm start nginx
```

---

## Windows Firewall Rules

| Rule Name | Port | Protocol | Direction | Action |
|---|---|---|---|---|
| Splunk HEC | 8088 | TCP | Inbound | Allow |
| Splunk Forwarder | 9997 | TCP | Inbound | Disabled |

---

## INetSim Log Forwarder

A Python script tails the INetSim service log and forwards events to Splunk HEC in real time.

### Script Location
`/tmp/inetsim_forwarder.py`

### Script Contents
```python
import time
import requests
import json

SPLUNK_HEC_URL = "https://192.168.1.54:8088/services/collector/event"
SPLUNK_TOKEN = "<token stored in Bitwarden>"
LOG_FILE = "/var/log/inetsim/service.log"

def send_to_splunk(event):
    payload = {
        "index": "malware-lab",
        "sourcetype": "inetsim:service",
        "event": event
    }
    try:
        requests.post(
            SPLUNK_HEC_URL,
            headers={"Authorization": "Splunk " + SPLUNK_TOKEN},
            json=payload,
            verify=False
        )
    except Exception as e:
        print("Error: " + str(e))

def tail_log(filepath):
    with open(filepath, 'r') as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if line:
                send_to_splunk(line.strip())
            else:
                time.sleep(1)

if __name__ == "__main__":
    print("Starting INetSim log forwarder...")
    tail_log(LOG_FILE)
```

### Running the Forwarder
```bash
sudo python3 /tmp/inetsim_forwarder.py &
```

### Dependencies
```bash
pip install requests --break-system-packages
```

---

## Splunk Searches

### View All Malware Lab Events
```
index=malware-lab
```

### View INetSim Service Events
```
index=malware-lab sourcetype=inetsim:service
```

### View Connections by Source IP
```
index=malware-lab sourcetype=inetsim:service | rex field=_raw "\[(?P<src_ip>\d+\.\d+\.\d+\.\d+)" | stats count by src_ip
```

### View by Protocol
```
index=malware-lab sourcetype=inetsim:service | rex field=_raw "\[(?P<protocol>\w+_\d+_\w+)" | stats count by protocol
```

---

## Known Issues

### Splunk HEC binds to loopback on Windows 11
Splunk 10.x on Windows 11 binds HEC to 127.0.0.1 regardless of bindAddress setting.
**Solution:** Use nginx as a reverse proxy as documented above.

### SSL certificate warnings from curl
INetSim uses self-signed certificates. Use `-k` flag with curl to bypass verification.
The forwarder script uses `verify=False` for the same reason.
