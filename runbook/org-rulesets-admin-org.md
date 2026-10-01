---
id: org-rulesets-admin-org
title: "Protect every default branch at once — org ruleset (needs admin:org; connector token cannot)"
surface: github
severity: high
tags: [github, org, rulesets, branch-protection, admin, enterprise]
last_verified: 2026-10-01
---
# Protect every default branch at once — org ruleset (needs admin:org; connector token cannot)

## Symptom
szl-org-health#176 found 52 of 97 active repositories without protected default branches; `.github#649` asks for exact-head gates on core mains. The connected automation token lacks `admin:org`, so `GET /orgs/szl-holdings/rulesets` returns 404 and org rulesets cannot be created by agents.

## Diagnose (PowerShell 5.1)
```powershell
gh auth status 2>&1 | Select-String "Token scopes"
gh api orgs/szl-holdings/rulesets 2>&1 | Select-Object -First 3
```

## Fix
```powershell
# Owner console (your own login, admin:org). Ruleset 1 is zero-risk: no deletes, no force-pushes on any default branch.
gh auth refresh -h github.com -s admin:org,repo,workflow
$Rules = @'
{ "name": "szl-default-branch-integrity", "target": "branch", "enforcement": "active",
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] },
                  "repository_name": { "include": ["~ALL"], "exclude": [], "protected": false } },
  "rules": [ { "type": "deletion" }, { "type": "non_fast_forward" } ],
  "bypass_actors": [ { "actor_id": 1, "actor_type": "OrganizationAdmin", "bypass_mode": "always" } ] }
'@
$Rules | gh api -X POST orgs/szl-holdings/rulesets --input -
# Ruleset 2 (flagships only): PRs required before merge on main; apps keep their lanes via bypass if needed.
$Flag = @'
{ "name": "szl-flagship-pr-required", "target": "branch", "enforcement": "active",
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] },
                  "repository_name": { "include": ["a11oy","killinchu","platform",".github","szl-router","david-leads","szl-substrate","szl-forge"], "exclude": [], "protected": false } },
  "rules": [ { "type": "pull_request", "parameters": { "required_approving_review_count": 0, "dismiss_stale_reviews_on_push": false, "require_code_owner_review": false, "require_last_push_approval": false, "required_review_thread_resolution": false } } ],
  "bypass_actors": [ { "actor_id": 1, "actor_type": "OrganizationAdmin", "bypass_mode": "pull_request" } ] }
'@
$Flag | gh api -X POST orgs/szl-holdings/rulesets --input -
```

## Verify
```powershell
gh api orgs/szl-holdings/rulesets --jq '.[]|"\(.id) \(.name) \(.enforcement)"'
gh api repos/szl-holdings/szl-pin/rules/branches/main --jq '.[].type'
```

## Notes
Org rulesets apply to repos the moment they are created (`~ALL`), which is how 52 repos get protected in one call and stay protected. Do not set required status checks org-wide: repos without those checks would never merge again. Enterprise plan, 3 seats, 2FA required, members cannot create public repos — confirmed 2026-10-01.

## Sources
- https://github.com/szl-holdings/szl-org-health/issues/176
- https://github.com/szl-holdings/.github/issues/649
