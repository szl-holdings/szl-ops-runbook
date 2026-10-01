---
id: security-gate-platform
title: "'Security Gate (blocking)' or 'Dependency Vulnerability Scan' red on platform — HIGH CVE in the pnpm tree"
surface: github
severity: high
tags: [github, platform, security, pnpm, grype, cve]
last_verified: 2026-10-01
---
# 'Security Gate (blocking)' or 'Dependency Vulnerability Scan' red on platform — HIGH CVE in the pnpm tree

## Symptom
platform PRs (#863, #601) fail `Dependency Vulnerability Scan` and `Security Gate (blocking)`; Grype/pnpm audit reports HIGH findings.

## Diagnose (PowerShell 5.1)
```powershell
$Root = (Resolve-Path -LiteralPath "$HOME\src\platform").Path; Set-Location -LiteralPath $Root
git fetch origin; git checkout <branch>
pnpm audit --audit-level high --json | ConvertFrom-Json | Select-Object -ExpandProperty advisories | Format-Table module_name, severity, patched_versions -AutoSize
```

## Fix
```powershell
# Pattern that cleared the last three waves (form-data, vite, nodemailer, undici): root pnpm overrides.
# package.json ->  "pnpm": { "overrides": { "<pkg>": ">=<fixed>" } }
pnpm install
pnpm audit --audit-level high
git add package.json pnpm-lock.yaml; git commit -s -m "fix(deps): override <pkg> to >=<fixed> (HIGH CVE)"; git push
```

## Verify
```powershell
gh pr checks <n> --repo szl-holdings/platform | Select-String "Security Gate|Vulnerability"
```

## Notes
If the vulnerable package is only reachable from a dev dependency, say so in the PR body under Security and keep the override anyway; the gate does not distinguish and the override is cheap.

## Sources
- https://github.com/szl-holdings/platform/pull/394
- https://github.com/szl-holdings/platform/pull/404
