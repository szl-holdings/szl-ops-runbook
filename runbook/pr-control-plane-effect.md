---
id: pr-control-plane-effect
title: "'Static control-plane effect boundary' fails — workflow/script change outside the admitted grammar"
surface: github
severity: high
tags: [github, .github, workflows, security, required-check]
last_verified: 2026-10-01
---
# 'Static control-plane effect boundary' fails — workflow/script change outside the admitted grammar

## Symptom
`Control-Plane Effect Gate` (CP-eBOM) reports `UNKNOWN_EFFECT` or a denied delta on a PR that edits `.github/workflows/*`, inline Python, shell, or repository scripts in `szl-holdings/.github`.

## Diagnose (PowerShell 5.1)
```powershell
$Root = (Resolve-Path -LiteralPath "$HOME\src\.github").Path; Set-Location -LiteralPath $Root
git fetch origin; git checkout <pr-head-branch>
python .github\scripts\control_plane_effect_gate.py --help
# Run the analyzer exactly as CI does (network-free); read cp-ebom\status.txt and the receipt delta it emits
python .github\scripts\control_plane_effect_gate.py --policy .github\data\control_plane_effect_policy.json --output cp-ebom
Get-Content cp-ebom\status.txt
```

## Fix
```powershell
# The gate is deliberately static and fail-closed. Three legitimate exits:
# 1. Split: move the effectful change (uploads, pushes, secret use, unpinned actions) into its own PR with a receipt.
# 2. Pin: every `uses:` must be an exact 40-hex SHA; every image an exact sha256 digest; secrets only via secrets.NAME.
# 3. Admit: if the command is genuinely new control-plane behavior, extend .github/data/control_plane_effect_policy.json
#    in the same PR and say so under 'Security' in the PR body. Never silence the gate by deleting it from required checks.
```

## Verify
```powershell
python .github\scripts\control_plane_effect_gate.py --policy .github\data\control_plane_effect_policy.json --output cp-ebom; Get-Content cp-ebom\status.txt
```

## Notes
Anything executable outside the recognized grammar is UNKNOWN_EFFECT and therefore denied. That is the design; it is not claiming formal verification. Docs-only PRs in `.github` (profile/, docs/) are typically unaffected unless they also touch workflows.

## Sources
- https://github.com/szl-holdings/.github/blob/main/.github/workflows/control-plane-effect-gate.yml
- https://github.com/szl-holdings/.github/blob/main/.github/scripts/control_plane_effect_gate.py
