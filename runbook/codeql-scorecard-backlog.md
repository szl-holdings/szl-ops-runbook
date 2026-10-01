---
id: codeql-scorecard-backlog
title: "Code-scanning backlog: 467 open alerts across 18 repos, 240 are PinnedDependenciesID — the wave plan"
surface: github
severity: high
tags: [security, codeql, scorecard, pinned-dependencies, token-permissions, ssrf, dangerous-workflow]
last_verified: 2026-10-01
---
# Code-scanning backlog: 467 open alerts across 18 repos, 240 are PinnedDependenciesID — the wave plan

## Symptom
Per-repo code-scanning counts at 2026-10-01: a11oy 100+ (list truncated), szl-forge 83, david-leads 76, killinchu 50, .github 50, vertical-services 38, immune 27, anatomy 22, szl-router 20. By rule: PinnedDependenciesID 240, TokenPermissionsID 40, py/empty-except 29, py/stack-trace-exposure 12, py/incomplete-url-substring-sanitization 8. Critical (7): DangerousWorkflowID in .github estate-one-fabric-alignment.yml (2), david-leads frontier-live-canary.yml (1), szl-router hf-space-drift-check.yml (1); py/partial-ssrf in david-leads app/signals.py:34, vertical-services services/finance/feed.py:35 and deploy/szl_verticals/connector_transport.py:27.

## Diagnose (PowerShell 5.1)
```powershell
foreach ($r in "a11oy","szl-forge","david-leads","killinchu",".github","vertical-services","immune","szl-router") {
  $items = gh api --paginate --slurp "repos/szl-holdings/$r/code-scanning/alerts?state=open&per_page=100" 2>$null | ConvertFrom-Json | ForEach-Object { $_ }
  $byRule = $items | Group-Object { $_.rule.id } | Sort-Object Count -Descending | Select-Object -First 5 | ForEach-Object { "$($_.Name)=$($_.Count)" }
  "{0,-18} open={1,-4} {2}" -f $r, @($items).Count, ($byRule -join " ")
}
```

## Fix
```powershell
# Wave order (highest risk first, each its own PR per repo, body with the seven provenance headings):
# 1. DangerousWorkflowID (critical): never run checked-out PR/workflow_run head code in a privileged context.
#    Pattern: checkout the TRUSTED base for scripts, pass untrusted head SHA only as data; or split into an unprivileged
#    pull_request job + a workflow_run job that only reads artifacts. Then dismiss remaining as 'used in tests' only with evidence.
# 2. py/partial-ssrf (critical): build outbound URLs from an allowlisted host table, never from request input; reject
#    anything not in the allowlist before the HTTP call (david-leads signals.py:34, vertical-services feed.py:35, connector_transport.py:27).
# 3. py/stack-trace-exposure (12): return a generic error body; log the traceback server-side with a correlation id.
# 4. TokenPermissionsID (40): top-level `permissions: {}` or `contents: read` in every workflow; grant per job.
# 5. PinnedDependenciesID (240): pin Docker base images by digest, pip installs with --require-hashes (pip-compile --generate-hashes),
#    GitHub Actions by 40-hex SHA (org rule already). Do it repo by repo; szl-forge (75) and .github (31) first.
# 6. Hygiene (py/empty-except 29, unused imports): ruff --fix in a dedicated PR per repo.
```

## Verify
```powershell
gh api "repos/szl-holdings/<repo>/code-scanning/alerts?state=open&per_page=1" --jq 'length'
```

## Notes
Scorecard findings (PinnedDependenciesID, TokenPermissionsID, FuzzingID, CIIBestPracticesID, CodeReviewID, MaintainedID) are posture probes, not exploitable bugs; the CodeQL py/* and DangerousWorkflowID findings are the ones that can hurt. Do not bulk-dismiss to make a number go green. Org-level code-scanning listing needs a security-manager token (401 at 2026-10-01); per-repo listing works.

## Sources
- https://github.com/szl-holdings/.github/security/code-scanning/263
- https://github.com/szl-holdings/david-leads/security/code-scanning/7
- https://github.com/szl-holdings/vertical-services/security/code-scanning/20
