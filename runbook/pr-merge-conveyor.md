---
id: pr-merge-conveyor
title: "Merge every green PR org-wide (squash), skip HOLD, log the rest — one block"
surface: github
severity: medium
tags: [github, pr, merge, conveyor, org-wide]
last_verified: 2026-10-01
---
# Merge every green PR org-wide (squash), skip HOLD, log the rest — one block

## Symptom
Open PRs are piling up across repos; you want everything that is MERGEABLE + CLEAN + non-draft + not HOLD-titled squash-merged now, and a list of what is left and why.

## Diagnose (PowerShell 5.1)
```powershell
gh search prs --owner szl-holdings --state open --limit 200 --json number,title,repository,isDraft,updatedAt |
  ConvertFrom-Json | Sort-Object updatedAt | Format-Table @{n='repo';e={$_.repository.nameWithOwner.Split('/')[1]}}, number, isDraft, @{n='title';e={$_.title.Substring(0,[Math]::Min(70,$_.title.Length))}} -AutoSize
```

## Fix
```powershell
$ErrorActionPreference = "Continue"
$Log = Join-Path $env:USERPROFILE ("szl-conveyor-" + (Get-Date -Format yyyyMMdd-HHmm) + ".log")
$Prs = gh search prs --owner szl-holdings --state open --limit 200 --json number,title,repository,isDraft | ConvertFrom-Json
foreach ($p in $Prs) {
  $repo = $p.repository.nameWithOwner; $n = $p.number
  if ($p.isDraft) { "SKIP draft    $repo#$n" | Tee-Object -FilePath $Log -Append; continue }
  if ($p.title -match '(?i)\bHOLD\b|Stephen decides') { "SKIP hold     $repo#$n" | Tee-Object -FilePath $Log -Append; continue }
  $v = gh pr view $n --repo $repo --json mergeable,mergeStateStatus,statusCheckRollup | ConvertFrom-Json
  $fails = @($v.statusCheckRollup | Where-Object { $_.conclusion -in 'FAILURE','TIMED_OUT','STARTUP_FAILURE' })
  if ($v.mergeable -eq 'MERGEABLE' -and $v.mergeStateStatus -in 'CLEAN','HAS_HOOKS' -and $fails.Count -eq 0) {
    gh pr merge $n --repo $repo --squash --delete-branch 2>&1 | Out-Null
    "MERGED        $repo#$n" | Tee-Object -FilePath $Log -Append
  } elseif ($v.mergeStateStatus -eq 'BEHIND' -and $fails.Count -eq 0) {
    gh pr update-branch $n --repo $repo --rebase 2>&1 | Out-Null
    "UPDATED       $repo#$n  (re-run conveyor in ~10 min)" | Tee-Object -FilePath $Log -Append
  } else {
    "LEFT          $repo#$n  mergeable=$($v.mergeable) state=$($v.mergeStateStatus) failing=$($fails.name -join ',')" | Tee-Object -FilePath $Log -Append
  }
}
"log: $Log"
```

## Verify
```powershell
gh search prs --owner szl-holdings --state open --limit 200 --json number --jq 'length'
```

## Notes
Never `--admin` past required checks on a11oy/killinchu/platform: the doctrine gates (truth-drift, parity, single-writer) are the product. The conveyor only merges what is already green. For `BEHIND` PRs it updates and asks you to re-run so provenance can re-evaluate.
