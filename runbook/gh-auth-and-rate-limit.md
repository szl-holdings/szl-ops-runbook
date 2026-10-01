---
id: gh-auth-and-rate-limit
title: "gh says 401/403 or 'rate limit exceeded' — refresh auth, check scopes, wait honestly"
surface: local
severity: medium
tags: [github, gh, auth, token, rate-limit]
last_verified: 2026-10-01
---
# gh says 401/403 or 'rate limit exceeded' — refresh auth, check scopes, wait honestly

## Symptom
`gh` calls fail with HTTP 401/403, `GraphQL: ... rate limit`, or `Resource not accessible by integration`.

## Diagnose (PowerShell 5.1)
```powershell
gh auth status 2>&1 | Select-String "Logged in|Token scopes|error"
gh api rate_limit --jq '{core:.resources.core, graphql:.resources.graphql, search:.resources.search}'
```

## Fix
```powershell
# Re-authenticate interactively (browser), adding the scopes the org tooling uses
gh auth refresh -h github.com -s repo,workflow,read:org,admin:org,read:packages
# If a stale GH_TOKEN env var is shadowing your login:
if ($env:GH_TOKEN) { Remove-Item Env:GH_TOKEN }  # for this session only
# Rate-limited: wait until reset; do not spin retries
$Reset = gh api rate_limit --jq '.resources.core.reset'; [DateTimeOffset]::FromUnixTimeSeconds($Reset).LocalDateTime
```

## Verify
```powershell
gh api user --jq .login; gh repo list szl-holdings --limit 1 --json name --jq '.[0].name'
```

## Notes
Org-admin actions (branch protection on 50+ repos, org secrets) need `admin:org`; a connector or app without it will report UNKNOWN, which is correct — do not read UNKNOWN as unprotected.

## Sources
- https://github.com/szl-holdings/szl-org-health/issues/176
