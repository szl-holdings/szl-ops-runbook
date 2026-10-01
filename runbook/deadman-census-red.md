---
id: deadman-census-red
title: "'Estate dead-man supervisor' / 'Estate readiness evidence' red — census fails closed on completeness"
surface: github
severity: medium
tags: [.github, szl-estate-os, szl-org-health, scheduler, census, credentials]
last_verified: 2026-10-01
---
# 'Estate dead-man supervisor' / 'Estate readiness evidence' red — census fails closed on completeness

## Symptom
Scheduled lanes fail every cycle: `.github` Estate dead-man supervisor, `szl-estate-os` Estate readiness evidence, `szl-frontier` Estate outside-seat verifier. Logs show tests green and then a final `exit 1` from the completeness gate (GitHub collection covered only a fallback subset, or no authenticated HF inventory reached the job).

## Diagnose (PowerShell 5.1)
```powershell
$Run = gh run list --repo szl-holdings/.github --workflow "Estate dead-man supervisor" --limit 1 --json databaseId --jq '.[0].databaseId'
gh run view $Run --repo szl-holdings/.github --log 2>$null | Select-String "UNKNOWN|fallback|subset|credential|HF_|token|incomplete" | Select-Object -Last 15
gh secret list --repo szl-holdings/.github --json name --jq '[.[].name]'
```

## Fix
```powershell
# Repair is credential-alias + scope alignment, never weakening the gate:
# - the job must receive the governed GitHub identity (SZL_GITHUB_TOKEN or the qillqaq App) with org read scope, and
# - an HF read token under the name the collector reads (check the workflow env block for the exact name).
gh secret set <NAME> --repo szl-holdings/.github   # value from secure prompt
gh workflow run "Estate dead-man supervisor" --repo szl-holdings/.github
```

## Verify
```powershell
gh run list --repo szl-holdings/.github --workflow "Estate dead-man supervisor" --limit 1 --json conclusion
```

## Notes
A healthy public-estate SRE run cannot clear a failed census; they are separately witnessed on purpose. szl-estate-os runs are not readable through `gh run view --log` when the job list is 404 (private + retention) — open the run URL instead.

## Sources
- https://github.com/szl-holdings/szl-org-health/issues/39
- https://github.com/szl-holdings/.github/issues/684
