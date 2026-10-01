---
id: hf-deploy-400-401-token
title: "HF Space/dataset deploy fails 400 Bad Request or 401 — HF_TOKEN missing or rotated"
surface: huggingface
severity: high
tags: [huggingface, github-actions, secrets, deploy, token]
last_verified: 2026-10-01
---
# HF Space/dataset deploy fails 400 Bad Request or 401 — HF_TOKEN missing or rotated

## Symptom
Reusable HF deployer prints `HF_TOKEN is not configured for the reusable deployer`, then `huggingface_hub.errors.BadRequestError ... 400` on `/api/spaces/SZLHOLDINGS/<space>/tree/main` (yarqa 2026-09-30, szl-gpu-bridge 2026-09-29). david-leads echoes `HTTP Error 401` from its dataset reader. Root cause on 2026-09-30: HF tokens were revoked and rotated; repository/org secrets still hold the old value or none.

## Diagnose (PowerShell 5.1)
```powershell
# Which repos declare the secret (names only, never values)
foreach ($r in "yarqa","szl-gpu-bridge","david-leads","puriq-live","sda","szl-sovereign-os","governance-as-code") {
  $names = gh secret list --repo "szl-holdings/$r" --json name --jq '[.[].name]' 2>$null
  "{0,-20} {1}" -f $r, $names
}
gh secret list --org szl-holdings --json name,visibility --jq '.[]|"\(.name) \(.visibility)"' 2>$null
# Is the token you hold valid and scoped to the org?
hf auth whoami 2>&1 | Select-Object -First 6
```

## Fix
```powershell
# 1. Mint ONE fine-grained HF token (write to the SZLHOLDINGS org repos that CI publishes). Store it once, org-wide:
#    (paste happens in the secure prompt; the value never lands in history)
$Tok = Read-Host -AsSecureString "Paste new HF write token"
$Plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Tok))
$Plain | gh secret set HF_TOKEN --org szl-holdings --visibility all
# Repos that use a differently named secret keep working only if you set that name too:
$Plain | gh secret set HF_ORG_TOKEN --org szl-holdings --visibility all
# david-leads reader (read-only, dataset-scoped token) is an ENVIRONMENT secret:
$Rd = Read-Host -AsSecureString "Paste DAVID_DATASET_READ_TOKEN (read-only)"
[Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Rd)) | gh secret set DAVID_DATASET_READ_TOKEN --repo szl-holdings/david-leads --env david-space-ci
Remove-Variable Plain, Tok, Rd
# 2. Re-run the failed lanes
gh run rerun (gh run list --repo szl-holdings/yarqa --workflow "HF Space deploy" --limit 1 --json databaseId --jq '.[0].databaseId') --repo szl-holdings/yarqa --failed
gh run rerun (gh run list --repo szl-holdings/szl-gpu-bridge --workflow "Sync training-receipts card" --limit 1 --json databaseId --jq '.[0].databaseId') --repo szl-holdings/szl-gpu-bridge --failed
```

## Verify
```powershell
gh run list --repo szl-holdings/yarqa --workflow "HF Space deploy" --limit 1 --json conclusion,url | ConvertFrom-Json
Invoke-WebRequest -UseBasicParsing -Method Head https://szlholdings-yarqa.hf.space/ | Select-Object StatusCode
```

## Notes
A 400 from `/tree/main?recursive=true` with huggingface_hub almost always means the request went out with an empty or invalid Authorization header, not a malformed path. Secret health in `.github` (secret-health.yml) reports PRESENT/MISSING/UNAVAILABLE by name; it cannot tell you a present token is dead — only a whoami or a rerun can.

## Sources
- https://github.com/szl-holdings/yarqa/actions/runs/36777783270
- https://github.com/szl-holdings/szl-gpu-bridge/actions/runs/36619758238
- https://github.com/szl-holdings/david-leads/actions/runs/36619707908
- https://github.com/szl-holdings/szl-doctrine/blob/main/FOUNDER_SECRETS_RUNBOOK.md
