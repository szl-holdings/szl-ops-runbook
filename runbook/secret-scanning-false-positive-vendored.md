---
id: secret-scanning-false-positive-vendored
title: "Secret-scanning alert points into vendored site-packages (committed venv) — verify, then resolve as false positive"
surface: github
severity: medium
tags: [security, secret-scanning, szl-forge, venv, false-positive]
last_verified: 2026-10-01
---
# Secret-scanning alert points into vendored site-packages (committed venv) — verify, then resolve as false positive

## Symptom
Secret scanning reports e.g. a 'Mistral AI API Key' in `.venv-chaski-r3-gpu/Lib/site-packages/transformers/...` (szl-forge alert #2, 2026-09-18). The 'secret' is a pattern match inside library source from a virtualenv that was committed once; validity shows `inactive`; the path is absent from HEAD.

## Diagnose (PowerShell 5.1)
```powershell
$Repo = "szl-holdings/szl-forge"; $N = 2
gh api "repos/$Repo/secret-scanning/alerts/$N" --jq '{state,validity,publicly_leaked,push_protection_bypassed,secret_type_display_name,html_url}'
gh api "repos/$Repo/secret-scanning/alerts/$N/locations" --jq '.[]|{type,path:.details.path,line:.details.start_line,commit:.details.commit_sha[0:10]}'
# Is the path still in HEAD? (404 = gone)
gh api "repos/$Repo/contents/.venv-chaski-r3-gpu" --jq 'if type=="array" then "PRESENT" else .message end'
```

## Fix
```powershell
# Only after the three facts above agree (validity inactive, path is library source, path absent from HEAD):
gh api -X PATCH "repos/$Repo/secret-scanning/alerts/$N" -f state=resolved -f resolution=false_positive -f resolution_comment="Pattern match inside vendored transformers source in a since-removed committed venv (commit 7dfba5d8); validity inactive; path absent from HEAD."
# If validity were 'active' or the match were in YOUR code: rotate the key at the provider FIRST, then resolve as 'revoked'.
# Keep venvs out of the tree for good (.gitignore already has .venv-ra-v2/, .venv-ra-v3/, khipu/.venv/):
Add-Content -LiteralPath .gitignore -Value ".venv*/"
```

## Verify
```powershell
gh api "repos/$Repo/secret-scanning/alerts?state=open" --jq 'length'
```

## Notes
This closure is a security decision; the audit agent prepares the evidence and the owner clicks. Org-wide at 2026-10-01 02:15Z: 1 open secret-scanning alert (this one), 1 open Dependabot alert (platform, npm, low). Push protection and secret scanning are enforced on every repo by managed configuration 252588.

## Sources
- https://github.com/szl-holdings/szl-forge/security/secret-scanning/2
