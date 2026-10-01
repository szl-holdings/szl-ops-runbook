---
id: org-profile-validators
title: "szl-holdings org profile red on Tests / SZL Router flagship alignment / estate alignment — required blocks and word budgets"
surface: github
severity: high
tags: [.github, profile, front-door, validators, org, huggingface-card]
last_verified: 2026-10-01
---
# szl-holdings org profile red on Tests / SZL Router flagship alignment / estate alignment — required blocks and word budgets

## Symptom
After editing `profile/README.md` (or `huggingface/org-card/README.md`), `.github` main goes red: `Tests` -> `truth boundary marker must remain on every front door: SIMULATED/HISTORICAL`; `SZL Router flagship alignment` -> `GitHub profile missing SZL Router ...`; `Exact taxonomy, front doors, and publication set` -> `GitHub profile missing Killinchu/Terra/PRISM Counsel/...`. This happened on 2026-10-01 after the 'AI that signs its work' rewrite.

## Diagnose (PowerShell 5.1)
```powershell
$Root = (Resolve-Path -LiteralPath "$HOME\src\.github").Path; Set-Location -LiteralPath $Root
git fetch origin; git checkout main; git pull --ff-only
(Get-Content profile\README.md -Raw).Split(" `n", [StringSplitOptions]::RemoveEmptyEntries).Count   # must be <= 430 words
(Get-Content huggingface\org-card\README.md -Raw).Split(" `n", [StringSplitOptions]::RemoveEmptyEntries).Count   # <= 380 words
python .github\scripts\public_front_door_check.py | Select-String '"state"|failures' -Context 0,6
python .github\scripts\router_flagship_contract.py | Select-String '"status"|missing'
python .github\scripts\estate_alignment_contract.py --output $env:TEMP\ea.json; (Get-Content $env:TEMP\ea.json | ConvertFrom-Json).failures
```

## Fix
```powershell
# The profile MUST contain all of these (case-insensitive where the script folds):
#  Router block : "SZL Router", "szl-holdings/szl-router", "SZLHOLDINGS/llm-router-live", "https://a-11-oy.com/code", "https://a11oy.net",
#                 "one inference flagship", "three commercial flagships", "five public domain bodies", "six internal engines",
#                 "not availability, operational readiness, or publication policy"
#  Truth markers: "Current state", "HISTORICAL", "SIMULATED"   (exact case; also required in the Hub card and the static front door HTML)
#  Historical contract: "16 portfolio Spaces", "1 inventory-only Space", "45 models", "34 datasets", and the names
#                 A11oy, Forge, Killinchu, Terra, PRISM Counsel, PURIQ Finance, LYTE
#  Canonical image: ./assets/evidence-lattice-v2.webp ; banned copy: "every model ships with signed receipts", "70+ live surfaces", "trust ceiling 0.97", "all models operational"
# A verified-passing profile (420 words, all three validators green locally on 2026-10-01) is kept at:
#   szl-ops-runbook/templates/org-profile-README.md
Copy-Item ..\szl-ops-runbook\templates\org-profile-README.md profile\README.md -Force
git checkout -b fix/profile-restore-required-blocks
git add profile\README.md; git commit -s -m "fix(profile): restore inference-flagship block, HISTORICAL contract, and truth-boundary markers"
git push -u origin fix/profile-restore-required-blocks
gh pr create --repo szl-holdings/.github --fill --body-file ..\szl-ops-runbook\templates\pr-body.md
```

## Verify
```powershell
python .github\scripts\public_front_door_check.py | Select-String '"state"'
python .github\scripts\router_flagship_contract.py | Select-String '"status"'
python .github\scripts\estate_alignment_contract.py --output $env:TEMP\ea.json; (Get-Content $env:TEMP\ea.json | ConvertFrom-Json).state
```

## Notes
Run the three scripts locally BEFORE pushing any profile or Hub-card copy change; they are fast and network-free. The Hub card has the same markers plus a 380-word budget, the 🛡️ emoji, a 60-char short description, and the router SVG URL. PR #816 restored only the markers and still failed the router and taxonomy gates — restore all three blocks together.

## Sources
- https://github.com/szl-holdings/.github/blob/main/.github/scripts/public_front_door_check.py
- https://github.com/szl-holdings/.github/blob/main/.github/scripts/router_flagship_contract.py
- https://github.com/szl-holdings/.github/actions/runs/36798458762
