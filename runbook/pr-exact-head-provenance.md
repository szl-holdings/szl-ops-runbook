---
id: pr-exact-head-provenance
title: "'Exact-head organization provenance' fails — PR is draft, behind, or forked"
surface: github
severity: high
tags: [github, pr, provenance, .github, required-check]
last_verified: 2026-10-01
---
# 'Exact-head organization provenance' fails — PR is draft, behind, or forked

## Symptom
Required check `Exact-head organization provenance` (from `.github/workflows/solo-builder-provenance.yml`) is red on an otherwise green PR. It fails whenever the PR is a draft, the base SHA no longer equals live `main`, `behind_by > 0`, or the head repo is not `szl-holdings/*`.

## Diagnose (PowerShell 5.1)
```powershell
$Repo = "szl-holdings/.github"; $Pr = 811
gh pr view $Pr --repo $Repo --json isDraft,mergeStateStatus,headRepository,baseRefName --jq '{draft:.isDraft,state:.mergeStateStatus,headRepo:.headRepository.name,base:.baseRefName}'
gh api "repos/$Repo/compare/main...$(gh pr view $Pr --repo $Repo --json headRefOid --jq .headRefOid)" --jq '{status,ahead_by,behind_by}'
```

## Fix
```powershell
# 1. Drafts always fail this gate. Mark ready when the PR is meant to merge:
gh pr ready $Pr --repo $Repo
# 2. Bring the head exactly on top of live main (behind_by must be 0):
gh pr update-branch $Pr --repo $Repo --rebase
# 3. Base must be main (or release/*) and head repo must be in the org — fork PRs are rejected by policy.
```

## Verify
```powershell
Start-Sleep -Seconds 90
gh pr checks $Pr --repo $Repo | Select-String "provenance"
```

## Notes
This gate runs on `pull_request_target` and re-evaluates on opened/synchronize/reopened/ready_for_review/edited. Converting to draft while you iterate is fine; just remember the gate stays red until `gh pr ready`. The merge-group variant requires the queue ref shape `gh-readonly-queue/main/pr-N-<sha>`.

## Sources
- https://github.com/szl-holdings/.github/blob/main/.github/workflows/solo-builder-provenance.yml
