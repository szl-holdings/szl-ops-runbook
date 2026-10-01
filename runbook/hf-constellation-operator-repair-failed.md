---
id: hf-constellation-operator-repair-failed
title: "'HF Living Constellation Operator' red: 'One or more public Spaces were not proven operational'"
surface: huggingface
severity: medium
tags: [huggingface, .github, scheduler, spaces, fleet]
last_verified: 2026-10-01
---
# 'HF Living Constellation Operator' red: 'One or more public Spaces were not proven operational'

## Symptom
Scheduled `.github` lane fails with `REPAIR_FAILED: 1` and the uploaded exact fleet receipt names the Space(s) that did not answer.

## Diagnose (PowerShell 5.1)
```powershell
$Run = gh run list --repo szl-holdings/.github --workflow "HF Living Constellation Operator" --limit 1 --json databaseId --jq '.[0].databaseId'
$Dir = Join-Path $env:TEMP "fleet-$Run"; gh run download $Run --repo szl-holdings/.github --dir $Dir 2>$null
Get-ChildItem $Dir -Recurse -Filter *.json | % { (Get-Content $_.FullName | ConvertFrom-Json).spaces | Where-Object { -not $_.operational } | Format-Table id, stage, http, reason -AutoSize }
```

## Fix
```powershell
# Usually one Space asleep or rebuilding: restart it (hf-space-paused-or-sleeping), then re-run the operator lane
gh workflow run "HF Living Constellation Operator" --repo szl-holdings/.github
```

## Verify
```powershell
gh run list --repo szl-holdings/.github --workflow "HF Living Constellation Operator" --limit 1 --json conclusion
```

## Notes
This lane fails closed by design; a 'green' that hides one dead Space would violate doctrine. Three consecutive scheduled receipts at 18/18 is the bar the Constellation project used for 'operational'.

## Sources
- https://github.com/szl-holdings/.github/actions/runs/36791432977
- https://github.com/szl-holdings/szl-constellation/issues/4
