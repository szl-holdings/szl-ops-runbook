---
id: codeql-triage
title: "CodeQL alerts — list, triage, and close with evidence"
surface: github
severity: medium
tags: [github, codeql, security, code-scanning]
last_verified: 2026-10-01
---
# CodeQL alerts — list, triage, and close with evidence

## Symptom
Code-scanning alerts accumulate (HTML sanitization, path injection, weak hashing, prompt injection, rate limiting). You want the open set per repo and a repeatable close path.

## Diagnose (PowerShell 5.1)
```powershell
foreach ($r in "a11oy","killinchu","platform","szl-router") {
  $alerts = gh api "repos/szl-holdings/$r/code-scanning/alerts?state=open&per_page=100" 2>$null | ConvertFrom-Json
  "{0,-12} open={1}" -f $r, @($alerts).Count
  $alerts | Group-Object { $_.rule.id } | Sort-Object Count -Descending | Select-Object -First 8 | Format-Table Count, Name -AutoSize
}
```

## Fix
```powershell
# Fix in code (preferred) and reference the alert number in the PR body under Security.
# Dismiss only with a reason that CodeQL accepts and a one-line justification:
gh api -X PATCH "repos/szl-holdings/<repo>/code-scanning/alerts/<n>" -f state=dismissed -f dismissed_reason="false positive" -f dismissed_comment="<why, with file:line>"
```

## Verify
```powershell
gh api "repos/szl-holdings/<repo>/code-scanning/alerts?state=open&per_page=1" --jq 'length'
```

## Notes
Org-level CodeQL is rolled out through the shared `.github` control plane and a managed org token; per-repo bespoke CodeQL workflows drift and should be removed in favor of the reusable one.

## Sources
- https://github.com/szl-holdings/.github/pull/584
