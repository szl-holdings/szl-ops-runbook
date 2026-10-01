---
id: pr-conflicting
title: "PR is CONFLICTING (DIRTY) — rebase and resolve, or close as net-zero"
surface: github
severity: medium
tags: [github, pr, rebase, conflicts]
last_verified: 2026-10-01
---
# PR is CONFLICTING (DIRTY) — rebase and resolve, or close as net-zero

## Symptom
`mergeable: CONFLICTING`, `mergeStateStatus: DIRTY`. Common on long-lived agent branches (e.g. platform#601 with 274 files, szl-energy-attest#47).

## Diagnose (PowerShell 5.1)
```powershell
$Repo = "szl-holdings/szl-energy-attest"; $Pr = 47
gh pr view $Pr --repo $Repo --json mergeable,mergeStateStatus,changedFiles,additions,deletions,headRefName | ConvertFrom-Json | Format-List
# Which files conflict?
$Head = gh pr view $Pr --repo $Repo --json headRefName --jq .headRefName
git fetch origin; git merge-tree (git merge-base origin/main origin/$Head) origin/main origin/$Head | Select-String "^<<<<<<<" | Measure-Object
```

## Fix
```powershell
# Option A — rebase and resolve
git checkout $Head
git rebase origin/main
# resolve each conflict, then:
git add -A; git rebase --continue
git push --force-with-lease origin $Head

# Option B — the PR's substance already landed on main through another PR (net-zero): close with a receipt comment
gh pr close $Pr --repo $Repo --comment "Closing as net-zero: substance landed on main via <sha/PR>. Diff against main after rebase was empty."
```

## Verify
```powershell
gh pr view $Pr --repo $Repo --json mergeable,mergeStateStatus --jq '.'
```

## Notes
Before Option B, prove net-zero: `git diff origin/main...origin/<head> --stat` after a trial rebase must be empty or whitespace-only. Record that in the close comment so the ledger is honest.
