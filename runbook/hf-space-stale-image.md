---
id: hf-space-stale-image
title: "Space reports RUNNING on the new commit but serves old code (routes 404) — factory rebuild"
surface: huggingface
severity: high
tags: [huggingface, space, docker, rebuild, killinchu, a11oy]
last_verified: 2026-10-01
---
# Space reports RUNNING on the new commit but serves old code (routes 404) — factory rebuild

## Symptom
GitHub `main` has the route; the live Space returns 404 for it; `/api/<app>/openapi.json` path count is lower than a local repro. Seen on killinchu 2026-06-05 (live 231 vs repro 250 paths) and again on 2026-07-06. Space UI says RUNNING at the new SHA.

## Diagnose (PowerShell 5.1)
```powershell
$Space = "SZLHOLDINGS/killinchu"; $Host = "szlholdings-killinchu.hf.space"
(Invoke-RestMethod "https://huggingface.co/api/spaces/$Space") | Select-Object sha, @{n='stage';e={$_.runtime.stage}}, lastModified
$Paths = (Invoke-RestMethod "https://$Host/api/killinchu/openapi.json").paths.PSObject.Properties.Name
"live openapi paths: $($Paths.Count)"
# Compare with what main declares (rough): count route decorators
gh api repos/szl-holdings/killinchu/contents/serve.py --jq .content | % { [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($_)) } | Select-String '@app\.(get|post|put|delete)\(' | Measure-Object
```

## Fix
```powershell
# Factory rebuild discards the cached image layers. Needs a write token for the org.
$Tok = Read-Host -AsSecureString "HF write token"
$H = @{ Authorization = "Bearer " + [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Tok)) }
Invoke-RestMethod -Method Post -Headers $H "https://huggingface.co/api/spaces/$Space/restart?factory=true"
Remove-Variable Tok, H
# Then poll (transient 000/5xx during rebuild is egress, not a crashed app — retry 3-6x)
1..12 | % { Start-Sleep 30; try { (Invoke-WebRequest -UseBasicParsing "https://$Host/healthz" -TimeoutSec 15).StatusCode } catch { "wait" } }
```

## Verify
```powershell
(Invoke-RestMethod "https://$Host/api/killinchu/openapi.json").paths.PSObject.Properties.Name.Count
```

## Notes
Diagnosis rule from KNOWN_GOTCHAS #9: 404 on a route whose code exists on main => check the deployed openapi path count against a local repro BEFORE suspecting a runtime exception. A failing register() leaves `NOT registered:` + traceback in Space logs; a clean boot with missing routes is a stale deploy. The HF Space git repo is distinct from GitHub main — a merge does not deploy by itself; the publisher lane does.

## Sources
- https://github.com/szl-holdings/killinchu/blob/main/KNOWN_GOTCHAS.md
