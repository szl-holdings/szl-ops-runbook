---
id: secret-health-unavailable
title: "secret-health reports UNAVAILABLE — qillqaq App permission, not a new PAT"
surface: github
severity: low
tags: [.github, secrets, qillqaq, github-app, policy]
last_verified: 2026-10-01
---
# secret-health reports UNAVAILABLE — qillqaq App permission, not a new PAT

## Symptom
`.github/workflows/secret-health.yml` reports required secret names as UNAVAILABLE across repos.

## Diagnose (PowerShell 5.1)
```powershell
gh run list --repo szl-holdings/.github --workflow "secret-health" --limit 1 --json conclusion,url | ConvertFrom-Json
gh api orgs/szl-holdings/installations --jq '.installations[]|{app_slug,permissions}' 2>$null
```

## Fix
```powershell
# Approve the qillqaq GitHub App's read-only Secrets permission upgrade in the org settings (owner action). No source change needed afterwards.
# Until then the lane falls back to SZL_GITHUB_TOKEN; keep that token governed. Do NOT mint another long-lived PAT for this audit.
```

## Verify
```powershell
gh workflow run secret-health.yml --repo szl-holdings/.github; Start-Sleep 120; gh run list --repo szl-holdings/.github --workflow "secret-health" --limit 1 --json conclusion
```

## Notes
UNAVAILABLE means 'could not read authoritatively'; it is never relabeled MISSING. Name presence does not prove a token is valid (see hf-deploy-400-401-token).

## Sources
- https://github.com/szl-holdings/szl-doctrine/blob/main/FOUNDER_SECRETS_RUNBOOK.md
