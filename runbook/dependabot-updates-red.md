---
id: dependabot-updates-red
title: "'Dependabot Updates' workflow is red — read the updater error, fix the lockfile, or ignore the ecosystem"
surface: github
severity: low
tags: [github, dependabot, pnpm, lockfile, ci]
last_verified: 2026-10-01
---
# 'Dependabot Updates' workflow is red — read the updater error, fix the lockfile, or ignore the ecosystem

## Symptom
Latest default-branch run of `Dependabot Updates` (event `dynamic`) is `failure` (seen on platform, immune, szl-frontier, a11oy-factory). The log ends with `Dependabot encountered '1' error(s) ... update_files`.

## Diagnose (PowerShell 5.1)
```powershell
$Repo = "szl-holdings/platform"
$Run = gh run list --repo $Repo --workflow "Dependabot Updates" --limit 1 --json databaseId --jq '.[0].databaseId'
gh run view $Run --repo $Repo --log-failed 2>$null | Select-String "error|Error|ERROR" | Select-Object -Last 15
```

## Fix
```powershell
# Typical causes in this estate:
# a) pnpm lockfile out of sync -> regenerate on the dev box and commit:
pnpm install --lockfile-only; git add pnpm-lock.yaml; git commit -s -m "chore(deps): resync pnpm lockfile"; git push
# b) private registry / unreachable package in a workspace -> add an `ignore:` for that ecosystem in .github/dependabot.yml
# c) Pure noise on an archived-in-practice repo -> set `open-pull-requests-limit: 0` for that ecosystem.
# Then re-run on demand:
gh api -X POST "repos/$Repo/dependabot/updates" 2>$null  # (no-op if unsupported; Dependabot reruns on schedule)
```

## Verify
```powershell
gh run list --repo $Repo --workflow "Dependabot Updates" --limit 3 --json conclusion,createdAt | ConvertFrom-Json | Format-Table
```

## Notes
A red Dependabot run does not block merges; it only means no dependency PRs were produced that cycle. Treat it as hygiene, not as an incident, unless the Security Gate also reports HIGH CVEs.
