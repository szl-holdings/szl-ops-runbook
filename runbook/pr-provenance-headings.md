---
id: pr-provenance-headings
title: "'szl/provenance' fails — PR body is missing the seven policy headings"
surface: github
severity: high
tags: [github, pr, provenance, pr-body, policy]
last_verified: 2026-10-01
---
# 'szl/provenance' fails — PR body is missing the seven policy headings

## Symptom
Check `szl/provenance` reports `pr_body_headings: false`. The solo-maintainer policy (`provenance/solo-maintainer-policy.v1.json`) requires the PR body to contain headings Origin, Rights, Agents and tools, Tests, Security, Rollback, Known limits.

## Diagnose (PowerShell 5.1)
```powershell
$Repo = "szl-holdings/.github"; $Pr = 815
$Body = gh pr view $Pr --repo $Repo --json body --jq .body
foreach ($h in "Origin","Rights","Agents and tools","Tests","Security","Rollback","Known limits") {
  $ok = $Body -match ('(?m)^#+\s*' + [regex]::Escape($h))
  "{0,-18} {1}" -f $h, $(if ($ok) {"present"} else {"MISSING"})
}
```

## Fix
```powershell
# Append the policy block to the existing body (does not delete what is there)
$Template = @'
## Origin
<what changed and why, one paragraph>

## Rights
Original work by the solo maintainer (stephenlutar2-hash); Apache-2.0 unless the repository states otherwise.

## Agents and tools
<Forge / Codex / Claude / Perplexity Computer / none> — human-reviewed before merge.

## Tests
<exact command(s) run and result>

## Security
<secrets touched: none | scanners: gitleaks/trivy/CodeQL result>

## Rollback
Revert this squash commit on main; no data migration.

## Known limits
<what this PR does not prove or change>
'@
$New = ($Body.TrimEnd() + "`n`n" + $Template)
$Tmp = Join-Path $env:TEMP "pr-body-$Pr.md"; Set-Content -LiteralPath $Tmp -Value $New -Encoding UTF8
gh pr edit $Pr --repo $Repo --body-file $Tmp
```

## Verify
```powershell
Start-Sleep -Seconds 60
gh pr checks $Pr --repo $Repo | Select-String "szl/provenance"
```

## Notes
Policy facts that bite: internal DCO is NOT required (solo build), external DCO/CLA is; merge mode is squash only; allowed human actor is `stephenlutar2-hash`; allowed app slugs are web-flow, dependabot, chatgpt-codex-connector. Save the template as a repo PR template to stop paying this tax: `.github/pull_request_template.md`.

## Sources
- https://github.com/szl-holdings/.github/blob/main/provenance/solo-maintainer-policy.v1.json
- https://github.com/szl-holdings/.github/blob/main/provenance/check.py
