---
id: pr-behind-main
title: "PR is BEHIND main — update the branch before anything else"
surface: github
severity: medium
tags: [github, pr, rebase, merge-queue]
last_verified: 2026-10-01
---
# PR is BEHIND main — update the branch before anything else

## Symptom
`gh pr view` shows `mergeStateStatus: BEHIND`; the Exact-head organization provenance gate fails because `behind_by != 0`; required checks look green but the merge button is blocked.

## Diagnose (PowerShell 5.1)
```powershell
$Repo = "szl-holdings/a11oy"; $Pr = 2373
gh pr view $Pr --repo $Repo --json number,isDraft,mergeable,mergeStateStatus,headRefName,baseRefName |
  ConvertFrom-Json | Format-List
```

## Fix
```powershell
# Fast path (GitHub does the merge-from-base commit; triggers 'synchronize' so provenance re-runs)
gh pr update-branch $Pr --repo $Repo --rebase

# If update-branch is rejected (branch protection or conflicts), rebase locally:
$Root = (Resolve-Path -LiteralPath "$HOME\src\a11oy").Path; Set-Location -LiteralPath $Root
git fetch origin
$Head = gh pr view $Pr --repo $Repo --json headRefName --jq .headRefName
git checkout $Head
git rebase origin/main
git push --force-with-lease origin $Head
```

## Verify
```powershell
gh pr view $Pr --repo $Repo --json mergeStateStatus,statusCheckRollup --jq '{state:.mergeStateStatus, failing:[.statusCheckRollup[]|select(.conclusion=="FAILURE")|.name]}'
```

## Notes
The `.github` provenance gate compares base SHA to the live `main` head at run time; a PR that was clean an hour ago fails again after any other merge to main. Update the branch immediately before merging, not earlier in the day.

## Sources
- https://github.com/szl-holdings/.github/blob/main/.github/workflows/solo-builder-provenance.yml
