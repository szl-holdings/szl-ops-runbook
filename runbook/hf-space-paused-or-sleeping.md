---
id: hf-space-paused-or-sleeping
title: "Free-tier Space paused or sleeping — restart it, then re-probe root and /healthz"
surface: huggingface
severity: medium
tags: [huggingface, space, restart, free-tier]
last_verified: 2026-10-01
---
# Free-tier Space paused or sleeping — restart it, then re-probe root and /healthz

## Symptom
Space page shows Paused/Sleeping; `*.hf.space` root returns 503 or a Hub placeholder; estate monitors mark it not operational (the Living Constellation Operator fails closed with REPAIR_FAILED).

## Diagnose (PowerShell 5.1)
```powershell
$Space = "SZLHOLDINGS/holographic"
(Invoke-RestMethod "https://huggingface.co/api/spaces/$Space").runtime | Select-Object stage, hardware
```

## Fix
```powershell
$Tok = Read-Host -AsSecureString "HF write token"
$H = @{ Authorization = "Bearer " + [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Tok)) }
Invoke-RestMethod -Method Post -Headers $H "https://huggingface.co/api/spaces/$Space/restart"
Remove-Variable Tok, H
```

## Verify
```powershell
$Sub = ($Space -replace '/','-').ToLower()
1..8 | % { Start-Sleep 20; try { (Invoke-WebRequest -UseBasicParsing "https://$Sub.hf.space/" -TimeoutSec 15).StatusCode } catch { "wait" } }
```

## Notes
Static Spaces live at `https://<org>-<name>.static.hf.space/`, not `.hf.space` — a 404 at `.hf.space` for a static Space is expected, not an outage (prove-it, governed-receipt-verifier, szl-bench-suite, szl-forge-lab, szl-brand-campaign, foundation-confirmation-v2).
