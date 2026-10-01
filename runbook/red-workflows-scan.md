---
id: red-workflows-scan
title: "Which workflows are red on main right now, org-wide — the one-block scan"
surface: github
severity: medium
tags: [github, ci, actions, org-wide, digest]
last_verified: 2026-10-01
---
# Which workflows are red on main right now, org-wide — the one-block scan

## Symptom
You need the latest-run-per-workflow on `main` for every active repo, filtered to failures, before deciding what to fix. (At the 2026-10-01 audit: 709 workflows scanned, 26 red across 20 repos.)

## Diagnose (PowerShell 5.1)
```powershell
$ErrorActionPreference = "Continue"
$Out = Join-Path $env:USERPROFILE ("szl-red-" + (Get-Date -Format yyyyMMdd) + ".csv")
$Repos = gh repo list szl-holdings --limit 300 --json name,isArchived | ConvertFrom-Json | Where-Object { -not $_.isArchived }
$Rows = foreach ($r in $Repos) {
  $runs = gh run list --repo "szl-holdings/$($r.name)" --branch main --limit 40 --json workflowName,conclusion,createdAt,url,event 2>$null | ConvertFrom-Json
  $seen = @{}
  foreach ($run in $runs) {
    if ($seen.ContainsKey($run.workflowName)) { continue }; $seen[$run.workflowName] = 1
    if ($run.conclusion -in 'failure','timed_out','startup_failure','action_required') {
      [pscustomobject]@{ repo=$r.name; workflow=$run.workflowName; conclusion=$run.conclusion; event=$run.event; when=$run.createdAt.Substring(0,10); url=$run.url }
    }
  }
}
$Rows | Sort-Object repo, workflow | Tee-Object -Variable Red | Export-Csv -NoTypeInformation -LiteralPath $Out
$Red | Format-Table repo, workflow, conclusion, event, when -AutoSize
"red workflows: $(@($Red).Count)  ->  $Out"
```

## Fix
```powershell
# For any row: pull the failing step lines
gh run view <databaseId-from-url> --repo szl-holdings/<repo> --log-failed 2>$null | Select-String "error|Error|Traceback|FAIL|401|400|404" | Select-Object -Last 20
```

## Verify
```powershell
# Re-run the scan; the count should drop. Scheduled lanes (dead-man, constellation operator) re-evaluate on their own cadence.
```

## Notes
Recurring classes seen 2026-10-01: HF deploy lanes failing on a missing/rotated HF_TOKEN (yarqa, szl-gpu-bridge, david-leads 401), Dependabot updater errors, estate schedulers failing closed on completeness, and the `.github` front-door validators after the profile rewrite. Each has its own entry here.

## Sources
- https://github.com/szl-holdings/.github/issues/158
