---
id: a11oy-parity-single-writer
title: "a11oy PRs fail 'Protected base matches immutable HF repository' / 'single-writer guard' / 'Shared source files in sync with killinchu'"
surface: github
severity: high
tags: [a11oy, killinchu, huggingface, parity, single-writer, required-check]
last_verified: 2026-10-01
---
# a11oy PRs fail 'Protected base matches immutable HF repository' / 'single-writer guard' / 'Shared source files in sync with killinchu'

## Symptom
One or more of: `Protected base matches immutable HF repository`, `canonical HF single-writer guard (stdlib, network-free)`, `Shared source files in sync with killinchu` red on an a11oy PR (#2386, #2360, #2318).

## Diagnose (PowerShell 5.1)
```powershell
$Repo = "szl-holdings/a11oy"; $Pr = 2360
gh pr checks $Pr --repo $Repo | Select-String "HF repository|single-writer|killinchu"
# Which shared files differ from killinchu?
$Root = (Resolve-Path -LiteralPath "$HOME\src\a11oy").Path; Set-Location -LiteralPath $Root
git fetch origin; git checkout (gh pr view $Pr --repo $Repo --json headRefName --jq .headRefName)
Get-Content .github\workflows\*.yml | Select-String "shared_source_sync|SHARED_FILES|killinchu" | Select-Object -First 8
```

## Fix
```powershell
# Parity/single-writer gates compare the PR base to the immutable Hub revision: a stale base fails even with a perfect diff.
gh pr update-branch $Pr --repo $Repo --rebase
# Shared-source drift: the shared modules are owned by szl-substrate / killinchu; re-copy from the owner rather than editing the a11oy copy.
# (the sync script prints the exact file list)
python scripts\check_shared_source_sync.py --fix 2>$null; git status --short
```

## Verify
```powershell
gh pr checks $Pr --repo $Repo | Select-String "HF repository|single-writer|killinchu"
```

## Notes
Issue a11oy#1615 recorded a logically unsatisfiable pair of pre-merge checks (one requiring a mirrored file to change, one requiring byte identity with main); the durable gate is a post-merge push-to-main parity check. Canonical sync owns the HF writes — never hand-push the a11oy Space while a PR is open.

## Sources
- https://github.com/szl-holdings/a11oy/issues/1615
- https://github.com/szl-holdings/a11oy/pull/1802
