---
id: hf-ecosystem-manifest-drift
title: "a11oy 'HF Ecosystem manifest drift' is red — regenerate the manifest, open the candidate PR"
surface: huggingface
severity: medium
tags: [huggingface, a11oy, manifest, drift, ci]
last_verified: 2026-10-01
---
# a11oy 'HF Ecosystem manifest drift' is red — regenerate the manifest, open the candidate PR

## Symptom
`HF Ecosystem manifest drift` fails on a11oy main after Hub counts change (e.g. 50/35/33). The collector prints a candidate manifest with `autoMerge:false, branchCreated:false` and exits 1.

## Diagnose (PowerShell 5.1)
```powershell
$Run = gh run list --repo szl-holdings/a11oy --workflow "HF Ecosystem manifest drift" --limit 1 --json databaseId,conclusion,url --jq '.[0]'
$Run
gh run view ($Run | ConvertFrom-Json).databaseId --repo szl-holdings/a11oy --log 2>$null | Select-String '"counts"' | Select-Object -Last 1
```

## Fix
```powershell
$Root = (Resolve-Path -LiteralPath "$HOME\src\a11oy").Path; Set-Location -LiteralPath $Root
git fetch origin; git checkout -b chore/hf-manifest-refresh origin/main
# the collector script is the one the workflow calls; run it the same way (see .github/workflows for the exact entrypoint)
Get-Content .github\workflows\hf-ecosystem-manifest-drift.yml | Select-String "run:|python" | Select-Object -First 12
python scripts\hf_ecosystem_manifest.py --write docs\huggingface-ecosystem-manifest.json   # adjust to the entrypoint printed above
git add docs\huggingface-ecosystem-manifest.json
git commit -s -m "chore(hf): refresh ecosystem manifest to observed Hub inventory"
git push -u origin chore/hf-manifest-refresh
gh pr create --repo szl-holdings/a11oy --fill --body-file ..\szl-ops-runbook\templates\pr-body.md
```

## Verify
```powershell
gh run list --repo szl-holdings/a11oy --workflow "HF Ecosystem manifest drift" --limit 1 --json conclusion
```

## Notes
The manifest is source-pinned on purpose: the org profile and Hub card link to a specific a11oy commit of this file. Refreshing it is a normal PR, not an emergency; the red run is the drift detector doing its job.

## Sources
- https://github.com/szl-holdings/a11oy/actions/runs/36796144190
