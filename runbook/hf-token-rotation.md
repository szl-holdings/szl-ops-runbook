---
id: hf-token-rotation
title: "Rotate Hugging Face tokens safely — revoke, mint fine-grained, re-seat, re-run"
surface: huggingface
severity: high
tags: [huggingface, token, rotation, secrets, security]
last_verified: 2026-10-01
---
# Rotate Hugging Face tokens safely — revoke, mint fine-grained, re-seat, re-run

## Symptom
A token was exposed, expired, or you are consolidating many tokens into one (the 2026-09-30 rotation: revoke hf_nGHC… and hf_rpzm…, keep one fresh token).

## Diagnose (PowerShell 5.1)
```powershell
hf auth whoami 2>&1 | Select-Object -First 8
gh secret list --org szl-holdings --json name --jq '[.[].name]'
```

## Fix
```powershell
# 1. In the Hub UI: Settings -> Access Tokens -> revoke old; create ONE fine-grained token:
#    repos: write on SZLHOLDINGS/* that CI publishes; no user-scope; name it by purpose + date.
# 2. Local login (browser flow; token never printed)
hf auth login --force
# 3. Seat it for CI (see hf-deploy-400-401-token) — org secret HF_TOKEN (+ HF_ORG_TOKEN alias where used)
# 4. Re-run the lanes that failed with 400/401.
```

## Verify
```powershell
hf auth whoami; gh run list --repo szl-holdings/yarqa --workflow "HF Space deploy" --limit 1 --json conclusion
```

## Notes
Prefer trusted publishing / OIDC where a lane supports it over long-lived tokens. Never paste a token into a chat, issue, or PR body; the runbook blocks read it with Read-Host -AsSecureString for that reason.

## Sources
- https://github.com/szl-holdings/szl-doctrine/blob/main/FOUNDER_SECRETS_RUNBOOK.md
