---
id: hf-space-config-error
title: "Space shows CONFIG_ERROR after a deploy — README front matter was overwritten"
surface: huggingface
severity: high
tags: [huggingface, space, readme, front-matter, reusable-hf-deploy]
last_verified: 2026-10-01
---
# Space shows CONFIG_ERROR after a deploy — README front matter was overwritten

## Symptom
Space stage `CONFIG_ERROR`; the Space README.md lost its YAML block (`sdk: docker`, `app_port`, `title`). Root cause tracked in `.github#193`: `reusable-hf-deploy` with `include-readme:false` still let a Dockerfile-derived README overwrite the card.

## Diagnose (PowerShell 5.1)
```powershell
$Space = "SZLHOLDINGS/<space>"
$Readme = Invoke-RestMethod "https://huggingface.co/spaces/$Space/raw/main/README.md"
if ($Readme -notmatch '(?s)^---\s*\n.*?\nsdk:\s*\w+') { "FRONT MATTER MISSING" } else { ($Readme -split "`n")[0..12] -join "`n" }
```

## Fix
```powershell
# Restore the card header from the GitHub source (space/README.md or the repo README with HF block), via the HF commit API.
$Tok = Read-Host -AsSecureString "HF write token"
$H = @{ Authorization = "Bearer " + [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Tok)) }
$Header = @"
---
title: <Title>
emoji: 🛡️
colorFrom: gray
colorTo: red
sdk: docker
app_port: 7860
pinned: false
---
"@
$Body = $Header + "`n" + ($Readme -replace '(?s)^---.*?---\s*', '')
# hf CLI does the multipart commit for you:
$Tmp = Join-Path $env:TEMP "README.md"; Set-Content -LiteralPath $Tmp -Value $Body -Encoding UTF8 -NoNewline
hf upload $Space $Tmp README.md --repo-type space --commit-message "fix(card): restore Space front matter"
Remove-Variable Tok, H
```

## Verify
```powershell
(Invoke-RestMethod "https://huggingface.co/api/spaces/$Space").runtime.stage
```

## Notes
Durable fix lives in the deployer: the Space card is a contract the publish lane must preserve (hatun-mcp#58 was the proximate recovery). If a repo's lane keeps clobbering the card, it is not using the canonical `reusable-hf-deploy` inputs correctly.

## Sources
- https://github.com/szl-holdings/.github/issues/193
- https://github.com/szl-holdings/hatun-mcp/pull/58
