---
id: own-metal-services
title: "Ollama / joule exporter / LiteLLM down behind a live tunnel (502/503/404) — restart the local stack"
surface: own-metal
severity: medium
tags: [own-metal, ollama, litellm, energy, exporter, scheduled-task]
last_verified: 2026-10-01
---
# Ollama / joule exporter / LiteLLM down behind a live tunnel (502/503/404) — restart the local stack

## Symptom
Tunnel host answers 502/503 (tunnel connected, local service down) or 404 (nothing on the port). `/api/a11oy/v1/code/health` on the product no longer says `self-hosted-gpu`.

## Diagnose (PowerShell 5.1)
```powershell
Get-Process ollama, cloudflared, python, litellm -ErrorAction SilentlyContinue | Select-Object ProcessName, Id, StartTime
Test-NetConnection 127.0.0.1 -Port 11434 -InformationLevel Quiet   # Ollama
Test-NetConnection 127.0.0.1 -Port 9471  -InformationLevel Quiet   # joule exporter
Test-NetConnection 127.0.0.1 -Port 4000  -InformationLevel Quiet   # LiteLLM
nvidia-smi --query-gpu=name,power.draw,memory.used --format=csv
```

## Fix
```powershell
# Preferred: the persisted scheduled tasks
Get-ScheduledTask -TaskName "*Ollama*","*Joule*","*LiteLLM*","*Tunnel*" -ErrorAction SilentlyContinue | Where-Object State -ne Running | Start-ScheduledTask
# Direct, if a task is missing:
Start-Process -WindowStyle Hidden -FilePath (Get-Command ollama).Source -ArgumentList "serve"
$Root = (Resolve-Path -LiteralPath "$HOME\src\a11oy").Path; Set-Location -LiteralPath $Root
Start-Process -WindowStyle Hidden python -ArgumentList "box-scripts\omen_joule_exporter.py"
Start-Process -WindowStyle Hidden litellm -ArgumentList "--config box-scripts\litellm_config.yaml --port 4000"
```

## Verify
```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags | Select-Object -ExpandProperty models | Select-Object name
(Invoke-RestMethod https://a-11-oy.com/api/a11oy/v1/code/health).inference
```

## Notes
Ollama stays tailnet-only — never expose 11434 through the tunnel. Energy claims: per-request joules are MEASURED only while the exporter and NVML are live; when they are not, the product must show UNAVAILABLE, and it does. Do not fake a healthy mesh in a demo.

## Sources
- https://github.com/szl-holdings/a11oy/blob/main/box-scripts/SZL_MESH_RESTART.ps1
- https://github.com/szl-holdings/platform/blob/main/replit-sync/FOUNDER_GPU_RUNBOOK.md
