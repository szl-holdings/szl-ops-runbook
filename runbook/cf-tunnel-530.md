---
id: cf-tunnel-530
title: "gpu / gateway / meter / meter2 .a-11-oy.com return 530 (error 1033) — cloudflared is down on the box"
surface: own-metal
severity: high
tags: [cloudflare, tunnel, own-metal, 530, 1033, omen, laptop]
last_verified: 2026-10-01
---
# gpu / gateway / meter / meter2 .a-11-oy.com return 530 (error 1033) — cloudflared is down on the box

## Symptom
Public probes: `https://gpu.a-11-oy.com/` -> 530, `gateway`/`meter`/`meter2` -> 530, while `gpu2` -> 403 (Cloudflare Access, expected). DNS still resolves to Cloudflare anycast. Observed 2026-10-01 01:10Z: all four tunnel hosts 530. Cause: cloudflared not connected (process down after reboot/sleep, or tunnel-ID drift in the CNAMEs).

## Diagnose (PowerShell 5.1)
```powershell
# From any machine: which hosts are down?
foreach ($h in "gateway","gpu","gpu2","meter","meter2","gdw","holdings") {
  try { $c = (Invoke-WebRequest -UseBasicParsing -Method Head "https://$h.a-11-oy.com/" -TimeoutSec 10).StatusCode } catch { $c = $_.Exception.Response.StatusCode.value__ }
  "{0,-8} {1}" -f $h, $c
}
# ON THE BOX (omen tower / betterwithage laptop), as Administrator:
cloudflared tunnel list
Get-Process cloudflared -ErrorAction SilentlyContinue | Select-Object Id, StartTime
Get-ScheduledTask -TaskName "*Tunnel*","*cloudflared*","*Ollama*","*Joule*","*LiteLLM*" -ErrorAction SilentlyContinue | Format-Table TaskName, State
```

## Fix
```powershell
# Run the repo scripts you already ship (a11oy/box-scripts). Admin PowerShell 5.1 on EACH box:
$Root = (Resolve-Path -LiteralPath "$HOME\src\a11oy").Path; Set-Location -LiteralPath $Root
git pull --ff-only
powershell -ExecutionPolicy RemoteSigned -File .\box-scripts\SZL_MESH_RESTART.ps1    # starts persisted tasks, cloudflared, Ollama; probes hosts
# If MESH_RESTART reports 530 persisting on a host whose local service is up, the CNAME points at a stale tunnel ID:
powershell -ExecutionPolicy RemoteSigned -File .\box-scripts\SZL_TUNNEL_HEAL.ps1     # re-routes ingress hostnames to THIS tunnel (uses local cert.pem, no API token)
# Nothing persisted at all? Re-run the boot persist script for the box:
#   tower : powershell -ExecutionPolicy RemoteSigned -File .\box-scripts\omen_boot_persist.ps1
#   laptop: powershell -ExecutionPolicy RemoteSigned -File .\box-scripts\laptop_persist.ps1
```

## Verify
```powershell
foreach ($h in "gateway","gpu","meter","meter2") { try { (Invoke-WebRequest -UseBasicParsing -Method Head "https://$h.a-11-oy.com/" -TimeoutSec 10).StatusCode } catch { "$h $($_.Exception.Response.StatusCode.value__)" } }
# 200 = up · 404 = tunnel up, nothing on the local port · 502/503 = tunnel up, local service down · 530 = tunnel not connected
```

## Notes
This is the one failure class no agent can fix remotely: it needs shell on the box (or a physical restart). Local services behind the tunnel: Ollama 11434 (tailnet only), joule exporter 9471, LiteLLM 4000. The gdw witness and holdings pages are NOT tunnel-backed, which is why they stay 200 while gpu is 530.

## Sources
- https://github.com/szl-holdings/a11oy/blob/main/box-scripts/SZL_MESH_RESTART.ps1
- https://github.com/szl-holdings/a11oy/blob/main/box-scripts/SZL_TUNNEL_HEAL.ps1
- https://github.com/szl-holdings/a11oy/blob/main/box-scripts/SOVEREIGN_MESH_RUNBOOK.md
