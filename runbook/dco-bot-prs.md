---
id: dco-bot-prs
title: "DCO blocks a Dependabot or bot PR — solo-build policy, not an admin bypass"
surface: github
severity: low
tags: [github, dco, dependabot, bots, policy]
last_verified: 2026-10-01
---
# DCO blocks a Dependabot or bot PR — solo-build policy, not an admin bypass

## Symptom
A bot-authored dependency PR cannot merge because its commits lack `Signed-off-by` while a DCO check is required (the a11oy#1236 pattern).

## Diagnose (PowerShell 5.1)
```powershell
gh pr view <n> --repo szl-holdings/<repo> --json author,commits --jq '{author:.author.login, unsigned:[.commits[]|select(.messageBody|test("Signed-off-by")|not)|.oid[0:7]]}'
```

## Fix
```powershell
# Policy already says internal DCO is not required for the solo maintainer (provenance/solo-maintainer-policy.v1.json).
# Durable fix per repo: make DCO non-required for bot actors or drop the legacy DCO check from branch protection,
# then rely on szl/provenance + squash merge (squash commit is authored by you and can carry the trailer).
# Your own commits — sign off at commit time:
git commit -s -m "fix: ..."
# Retro-fit sign-off on a branch you own:
git rebase --signoff origin/main; git push --force-with-lease
```

## Verify
```powershell
gh pr checks <n> --repo szl-holdings/<repo>
```

## Notes
Do not restore a hard DCO requirement and then admin-bypass it; either the policy requires it or it does not. The honest state for this org: bot PRs pass via allowed app slugs (dependabot, chatgpt-codex-connector), humans pass via the solo-maintainer allowlist.

## Sources
- https://github.com/szl-holdings/.github/blob/main/provenance/solo-maintainer-policy.v1.json
