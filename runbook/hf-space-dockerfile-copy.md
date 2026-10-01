---
id: hf-space-dockerfile-copy
title: "New organ/module 404s on the Space although the file synced — Dockerfile COPY discipline"
surface: huggingface
severity: medium
tags: [huggingface, space, dockerfile, killinchu, a11oy, organs]
last_verified: 2026-10-01
---
# New organ/module 404s on the Space although the file synced — Dockerfile COPY discipline

## Symptom
A new `szl_<name>.py` organ is in the Space repo but its endpoint returns 404; the image never contained the file because the live Space Dockerfile has per-file `COPY` lines and the new one was never added.

## Diagnose (PowerShell 5.1)
```powershell
$Space = "SZLHOLDINGS/killinchu"
$Df = Invoke-RestMethod "https://huggingface.co/spaces/$Space/raw/main/Dockerfile"
$Df -split "`n" | Select-String '^\s*COPY\s+szl_' | % { $_.Line.Trim() }
```

## Fix
```powershell
# Add the COPY line to the LIVE Space Dockerfile (it diverges from the GitHub Dockerfile by design):
#   COPY szl_<name>.py ./
# Commit via hf CLI, then factory rebuild (see hf-space-stale-image).
$Tmp = Join-Path $env:TEMP "Dockerfile"; Set-Content -LiteralPath $Tmp -Value ($Df.TrimEnd() + "`nCOPY szl_<name>.py ./`n") -Encoding ASCII -NoNewline
hf upload $Space $Tmp Dockerfile --repo-type space --commit-message "build: COPY szl_<name>.py into image"
```

## Verify
```powershell
Invoke-RestMethod "https://szlholdings-killinchu.hf.space/api/killinchu/v1/<name>/health"
```

## Notes
Two more killinchu gotchas that crashed the Space before: the serve.py register block must write to `sys.stderr`, never `_frontier_sys` (undefined alias — wave 13 crash); and never `from __future__ import annotations` in files that define FastAPI routes or Pydantic models.

## Sources
- https://github.com/szl-holdings/killinchu/blob/main/KNOWN_GOTCHAS.md
