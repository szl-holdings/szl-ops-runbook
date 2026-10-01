# Runbook entries — part A: GitHub / PR flow. Each entry renders to runbook/<id>.md
ENTRIES = []

def add(**kw):
    ENTRIES.append(kw)

PR_BODY_TEMPLATE = r'''## Origin
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
<what this PR does not prove or change>'''

add(
    id="pr-behind-main",
    title="PR is BEHIND main — update the branch before anything else",
    tags=["github", "pr", "rebase", "merge-queue"],
    surface="github",
    severity="medium",
    symptom="`gh pr view` shows `mergeStateStatus: BEHIND`; the Exact-head organization provenance gate fails because `behind_by != 0`; required checks look green but the merge button is blocked.",
    diagnose=r'''$Repo = "szl-holdings/a11oy"; $Pr = 2373
gh pr view $Pr --repo $Repo --json number,isDraft,mergeable,mergeStateStatus,headRefName,baseRefName |
  ConvertFrom-Json | Format-List''',
    fix=r'''# Fast path (GitHub does the merge-from-base commit; triggers 'synchronize' so provenance re-runs)
gh pr update-branch $Pr --repo $Repo --rebase

# If update-branch is rejected (branch protection or conflicts), rebase locally:
$Root = (Resolve-Path -LiteralPath "$HOME\src\a11oy").Path; Set-Location -LiteralPath $Root
git fetch origin
$Head = gh pr view $Pr --repo $Repo --json headRefName --jq .headRefName
git checkout $Head
git rebase origin/main
git push --force-with-lease origin $Head''',
    verify=r'''gh pr view $Pr --repo $Repo --json mergeStateStatus,statusCheckRollup --jq '{state:.mergeStateStatus, failing:[.statusCheckRollup[]|select(.conclusion=="FAILURE")|.name]}' ''',
    notes="The `.github` provenance gate compares base SHA to the live `main` head at run time; a PR that was clean an hour ago fails again after any other merge to main. Update the branch immediately before merging, not earlier in the day.",
    sources=["https://github.com/szl-holdings/.github/blob/main/.github/workflows/solo-builder-provenance.yml"],
)

add(
    id="pr-conflicting",
    title="PR is CONFLICTING (DIRTY) — rebase and resolve, or close as net-zero",
    tags=["github", "pr", "rebase", "conflicts"],
    surface="github",
    severity="medium",
    symptom="`mergeable: CONFLICTING`, `mergeStateStatus: DIRTY`. Common on long-lived agent branches (e.g. platform#601 with 274 files, szl-energy-attest#47).",
    diagnose=r'''$Repo = "szl-holdings/szl-energy-attest"; $Pr = 47
gh pr view $Pr --repo $Repo --json mergeable,mergeStateStatus,changedFiles,additions,deletions,headRefName | ConvertFrom-Json | Format-List
# Which files conflict?
$Head = gh pr view $Pr --repo $Repo --json headRefName --jq .headRefName
git fetch origin; git merge-tree (git merge-base origin/main origin/$Head) origin/main origin/$Head | Select-String "^<<<<<<<" | Measure-Object''',
    fix=r'''# Option A — rebase and resolve
git checkout $Head
git rebase origin/main
# resolve each conflict, then:
git add -A; git rebase --continue
git push --force-with-lease origin $Head

# Option B — the PR's substance already landed on main through another PR (net-zero): close with a receipt comment
gh pr close $Pr --repo $Repo --comment "Closing as net-zero: substance landed on main via <sha/PR>. Diff against main after rebase was empty."''',
    verify=r'''gh pr view $Pr --repo $Repo --json mergeable,mergeStateStatus --jq '.' ''',
    notes="Before Option B, prove net-zero: `git diff origin/main...origin/<head> --stat` after a trial rebase must be empty or whitespace-only. Record that in the close comment so the ledger is honest.",
    sources=[],
)

add(
    id="pr-exact-head-provenance",
    title="'Exact-head organization provenance' fails — PR is draft, behind, or forked",
    tags=["github", "pr", "provenance", ".github", "required-check"],
    surface="github",
    severity="high",
    symptom="Required check `Exact-head organization provenance` (from `.github/workflows/solo-builder-provenance.yml`) is red on an otherwise green PR. It fails whenever the PR is a draft, the base SHA no longer equals live `main`, `behind_by > 0`, or the head repo is not `szl-holdings/*`.",
    diagnose=r'''$Repo = "szl-holdings/.github"; $Pr = 811
gh pr view $Pr --repo $Repo --json isDraft,mergeStateStatus,headRepository,baseRefName --jq '{draft:.isDraft,state:.mergeStateStatus,headRepo:.headRepository.name,base:.baseRefName}'
gh api "repos/$Repo/compare/main...$(gh pr view $Pr --repo $Repo --json headRefOid --jq .headRefOid)" --jq '{status,ahead_by,behind_by}' ''',
    fix=r'''# 1. Drafts always fail this gate. Mark ready when the PR is meant to merge:
gh pr ready $Pr --repo $Repo
# 2. Bring the head exactly on top of live main (behind_by must be 0):
gh pr update-branch $Pr --repo $Repo --rebase
# 3. Base must be main (or release/*) and head repo must be in the org — fork PRs are rejected by policy.''',
    verify=r'''Start-Sleep -Seconds 90
gh pr checks $Pr --repo $Repo | Select-String "provenance" ''',
    notes="This gate runs on `pull_request_target` and re-evaluates on opened/synchronize/reopened/ready_for_review/edited. Converting to draft while you iterate is fine; just remember the gate stays red until `gh pr ready`. The merge-group variant requires the queue ref shape `gh-readonly-queue/main/pr-N-<sha>`.",
    sources=["https://github.com/szl-holdings/.github/blob/main/.github/workflows/solo-builder-provenance.yml"],
)

add(
    id="pr-provenance-headings",
    title="'szl/provenance' fails — PR body is missing the seven policy headings",
    tags=["github", "pr", "provenance", "pr-body", "policy"],
    surface="github",
    severity="high",
    symptom="Check `szl/provenance` reports `pr_body_headings: false`. The solo-maintainer policy (`provenance/solo-maintainer-policy.v1.json`) requires the PR body to contain headings Origin, Rights, Agents and tools, Tests, Security, Rollback, Known limits.",
    diagnose=r'''$Repo = "szl-holdings/.github"; $Pr = 815
$Body = gh pr view $Pr --repo $Repo --json body --jq .body
foreach ($h in "Origin","Rights","Agents and tools","Tests","Security","Rollback","Known limits") {
  $ok = $Body -match ('(?m)^#+\s*' + [regex]::Escape($h))
  "{0,-18} {1}" -f $h, $(if ($ok) {"present"} else {"MISSING"})
}''',
    fix=r'''# Append the policy block to the existing body (does not delete what is there)
$Template = @'
''' + PR_BODY_TEMPLATE + r'''
'@
$New = ($Body.TrimEnd() + "`n`n" + $Template)
$Tmp = Join-Path $env:TEMP "pr-body-$Pr.md"; Set-Content -LiteralPath $Tmp -Value $New -Encoding UTF8
gh pr edit $Pr --repo $Repo --body-file $Tmp''',
    verify=r'''Start-Sleep -Seconds 60
gh pr checks $Pr --repo $Repo | Select-String "szl/provenance" ''',
    notes="Policy facts that bite: internal DCO is NOT required (solo build), external DCO/CLA is; merge mode is squash only; allowed human actor is `stephenlutar2-hash`; allowed app slugs are web-flow, dependabot, chatgpt-codex-connector. Save the template as a repo PR template to stop paying this tax: `.github/pull_request_template.md`.",
    sources=["https://github.com/szl-holdings/.github/blob/main/provenance/solo-maintainer-policy.v1.json", "https://github.com/szl-holdings/.github/blob/main/provenance/check.py"],
)

add(
    id="pr-control-plane-effect",
    title="'Static control-plane effect boundary' fails — workflow/script change outside the admitted grammar",
    tags=["github", ".github", "workflows", "security", "required-check"],
    surface="github",
    severity="high",
    symptom="`Control-Plane Effect Gate` (CP-eBOM) reports `UNKNOWN_EFFECT` or a denied delta on a PR that edits `.github/workflows/*`, inline Python, shell, or repository scripts in `szl-holdings/.github`.",
    diagnose=r'''$Root = (Resolve-Path -LiteralPath "$HOME\src\.github").Path; Set-Location -LiteralPath $Root
git fetch origin; git checkout <pr-head-branch>
python .github\scripts\control_plane_effect_gate.py --help
# Run the analyzer exactly as CI does (network-free); read cp-ebom\status.txt and the receipt delta it emits
python .github\scripts\control_plane_effect_gate.py --policy .github\data\control_plane_effect_policy.json --output cp-ebom
Get-Content cp-ebom\status.txt''',
    fix=r'''# The gate is deliberately static and fail-closed. Three legitimate exits:
# 1. Split: move the effectful change (uploads, pushes, secret use, unpinned actions) into its own PR with a receipt.
# 2. Pin: every `uses:` must be an exact 40-hex SHA; every image an exact sha256 digest; secrets only via secrets.NAME.
# 3. Admit: if the command is genuinely new control-plane behavior, extend .github/data/control_plane_effect_policy.json
#    in the same PR and say so under 'Security' in the PR body. Never silence the gate by deleting it from required checks.''',
    verify=r'''python .github\scripts\control_plane_effect_gate.py --policy .github\data\control_plane_effect_policy.json --output cp-ebom; Get-Content cp-ebom\status.txt''',
    notes="Anything executable outside the recognized grammar is UNKNOWN_EFFECT and therefore denied. That is the design; it is not claiming formal verification. Docs-only PRs in `.github` (profile/, docs/) are typically unaffected unless they also touch workflows.",
    sources=["https://github.com/szl-holdings/.github/blob/main/.github/workflows/control-plane-effect-gate.yml", "https://github.com/szl-holdings/.github/blob/main/.github/scripts/control_plane_effect_gate.py"],
)

add(
    id="pr-merge-conveyor",
    title="Merge every green PR org-wide (squash), skip HOLD, log the rest — one block",
    tags=["github", "pr", "merge", "conveyor", "org-wide"],
    surface="github",
    severity="medium",
    symptom="Open PRs are piling up across repos; you want everything that is MERGEABLE + CLEAN + non-draft + not HOLD-titled squash-merged now, and a list of what is left and why.",
    diagnose=r'''gh search prs --owner szl-holdings --state open --limit 200 --json number,title,repository,isDraft,updatedAt |
  ConvertFrom-Json | Sort-Object updatedAt | Format-Table @{n='repo';e={$_.repository.nameWithOwner.Split('/')[1]}}, number, isDraft, @{n='title';e={$_.title.Substring(0,[Math]::Min(70,$_.title.Length))}} -AutoSize''',
    fix=r'''$ErrorActionPreference = "Continue"
$Log = Join-Path $env:USERPROFILE ("szl-conveyor-" + (Get-Date -Format yyyyMMdd-HHmm) + ".log")
$Prs = gh search prs --owner szl-holdings --state open --limit 200 --json number,title,repository,isDraft | ConvertFrom-Json
foreach ($p in $Prs) {
  $repo = $p.repository.nameWithOwner; $n = $p.number
  if ($p.isDraft) { "SKIP draft    $repo#$n" | Tee-Object -FilePath $Log -Append; continue }
  if ($p.title -match '(?i)\bHOLD\b|Stephen decides') { "SKIP hold     $repo#$n" | Tee-Object -FilePath $Log -Append; continue }
  $v = gh pr view $n --repo $repo --json mergeable,mergeStateStatus,statusCheckRollup | ConvertFrom-Json
  $fails = @($v.statusCheckRollup | Where-Object { $_.conclusion -in 'FAILURE','TIMED_OUT','STARTUP_FAILURE' })
  if ($v.mergeable -eq 'MERGEABLE' -and $v.mergeStateStatus -in 'CLEAN','HAS_HOOKS' -and $fails.Count -eq 0) {
    gh pr merge $n --repo $repo --squash --delete-branch 2>&1 | Out-Null
    "MERGED        $repo#$n" | Tee-Object -FilePath $Log -Append
  } elseif ($v.mergeStateStatus -eq 'BEHIND' -and $fails.Count -eq 0) {
    gh pr update-branch $n --repo $repo --rebase 2>&1 | Out-Null
    "UPDATED       $repo#$n  (re-run conveyor in ~10 min)" | Tee-Object -FilePath $Log -Append
  } else {
    "LEFT          $repo#$n  mergeable=$($v.mergeable) state=$($v.mergeStateStatus) failing=$($fails.name -join ',')" | Tee-Object -FilePath $Log -Append
  }
}
"log: $Log"''',
    verify=r'''gh search prs --owner szl-holdings --state open --limit 200 --json number --jq 'length' ''',
    notes="Never `--admin` past required checks on a11oy/killinchu/platform: the doctrine gates (truth-drift, parity, single-writer) are the product. The conveyor only merges what is already green. For `BEHIND` PRs it updates and asks you to re-run so provenance can re-evaluate.",
    sources=[],
)

add(
    id="dco-bot-prs",
    title="DCO blocks a Dependabot or bot PR — solo-build policy, not an admin bypass",
    tags=["github", "dco", "dependabot", "bots", "policy"],
    surface="github",
    severity="low",
    symptom="A bot-authored dependency PR cannot merge because its commits lack `Signed-off-by` while a DCO check is required (the a11oy#1236 pattern).",
    diagnose=r'''gh pr view <n> --repo szl-holdings/<repo> --json author,commits --jq '{author:.author.login, unsigned:[.commits[]|select(.messageBody|test("Signed-off-by")|not)|.oid[0:7]]}' ''',
    fix=r'''# Policy already says internal DCO is not required for the solo maintainer (provenance/solo-maintainer-policy.v1.json).
# Durable fix per repo: make DCO non-required for bot actors or drop the legacy DCO check from branch protection,
# then rely on szl/provenance + squash merge (squash commit is authored by you and can carry the trailer).
# Your own commits — sign off at commit time:
git commit -s -m "fix: ..."
# Retro-fit sign-off on a branch you own:
git rebase --signoff origin/main; git push --force-with-lease''',
    verify=r'''gh pr checks <n> --repo szl-holdings/<repo>''',
    notes="Do not restore a hard DCO requirement and then admin-bypass it; either the policy requires it or it does not. The honest state for this org: bot PRs pass via allowed app slugs (dependabot, chatgpt-codex-connector), humans pass via the solo-maintainer allowlist.",
    sources=["https://github.com/szl-holdings/.github/blob/main/provenance/solo-maintainer-policy.v1.json"],
)

add(
    id="dependabot-updates-red",
    title="'Dependabot Updates' workflow is red — read the updater error, fix the lockfile, or ignore the ecosystem",
    tags=["github", "dependabot", "pnpm", "lockfile", "ci"],
    surface="github",
    severity="low",
    symptom="Latest default-branch run of `Dependabot Updates` (event `dynamic`) is `failure` (seen on platform, immune, szl-frontier, a11oy-factory). The log ends with `Dependabot encountered '1' error(s) ... update_files`.",
    diagnose=r'''$Repo = "szl-holdings/platform"
$Run = gh run list --repo $Repo --workflow "Dependabot Updates" --limit 1 --json databaseId --jq '.[0].databaseId'
gh run view $Run --repo $Repo --log-failed 2>$null | Select-String "error|Error|ERROR" | Select-Object -Last 15''',
    fix=r'''# Typical causes in this estate:
# a) pnpm lockfile out of sync -> regenerate on the dev box and commit:
pnpm install --lockfile-only; git add pnpm-lock.yaml; git commit -s -m "chore(deps): resync pnpm lockfile"; git push
# b) private registry / unreachable package in a workspace -> add an `ignore:` for that ecosystem in .github/dependabot.yml
# c) Pure noise on an archived-in-practice repo -> set `open-pull-requests-limit: 0` for that ecosystem.
# Then re-run on demand:
gh api -X POST "repos/$Repo/dependabot/updates" 2>$null  # (no-op if unsupported; Dependabot reruns on schedule)''',
    verify=r'''gh run list --repo $Repo --workflow "Dependabot Updates" --limit 3 --json conclusion,createdAt | ConvertFrom-Json | Format-Table''',
    notes="A red Dependabot run does not block merges; it only means no dependency PRs were produced that cycle. Treat it as hygiene, not as an incident, unless the Security Gate also reports HIGH CVEs.",
    sources=[],
)

add(
    id="security-gate-platform",
    title="'Security Gate (blocking)' or 'Dependency Vulnerability Scan' red on platform — HIGH CVE in the pnpm tree",
    tags=["github", "platform", "security", "pnpm", "grype", "cve"],
    surface="github",
    severity="high",
    symptom="platform PRs (#863, #601) fail `Dependency Vulnerability Scan` and `Security Gate (blocking)`; Grype/pnpm audit reports HIGH findings.",
    diagnose=r'''$Root = (Resolve-Path -LiteralPath "$HOME\src\platform").Path; Set-Location -LiteralPath $Root
git fetch origin; git checkout <branch>
pnpm audit --audit-level high --json | ConvertFrom-Json | Select-Object -ExpandProperty advisories | Format-Table module_name, severity, patched_versions -AutoSize''',
    fix=r'''# Pattern that cleared the last three waves (form-data, vite, nodemailer, undici): root pnpm overrides.
# package.json ->  "pnpm": { "overrides": { "<pkg>": ">=<fixed>" } }
pnpm install
pnpm audit --audit-level high
git add package.json pnpm-lock.yaml; git commit -s -m "fix(deps): override <pkg> to >=<fixed> (HIGH CVE)"; git push''',
    verify=r'''gh pr checks <n> --repo szl-holdings/platform | Select-String "Security Gate|Vulnerability" ''',
    notes="If the vulnerable package is only reachable from a dev dependency, say so in the PR body under Security and keep the override anyway; the gate does not distinguish and the override is cheap.",
    sources=["https://github.com/szl-holdings/platform/pull/394", "https://github.com/szl-holdings/platform/pull/404"],
)

add(
    id="codeql-triage",
    title="CodeQL alerts — list, triage, and close with evidence",
    tags=["github", "codeql", "security", "code-scanning"],
    surface="github",
    severity="medium",
    symptom="Code-scanning alerts accumulate (HTML sanitization, path injection, weak hashing, prompt injection, rate limiting). You want the open set per repo and a repeatable close path.",
    diagnose=r'''foreach ($r in "a11oy","killinchu","platform","szl-router") {
  $alerts = gh api "repos/szl-holdings/$r/code-scanning/alerts?state=open&per_page=100" 2>$null | ConvertFrom-Json
  "{0,-12} open={1}" -f $r, @($alerts).Count
  $alerts | Group-Object { $_.rule.id } | Sort-Object Count -Descending | Select-Object -First 8 | Format-Table Count, Name -AutoSize
}''',
    fix=r'''# Fix in code (preferred) and reference the alert number in the PR body under Security.
# Dismiss only with a reason that CodeQL accepts and a one-line justification:
gh api -X PATCH "repos/szl-holdings/<repo>/code-scanning/alerts/<n>" -f state=dismissed -f dismissed_reason="false positive" -f dismissed_comment="<why, with file:line>"''',
    verify=r'''gh api "repos/szl-holdings/<repo>/code-scanning/alerts?state=open&per_page=1" --jq 'length' ''',
    notes="Org-level CodeQL is rolled out through the shared `.github` control plane and a managed org token; per-repo bespoke CodeQL workflows drift and should be removed in favor of the reusable one.",
    sources=["https://github.com/szl-holdings/.github/pull/584"],
)

add(
    id="red-workflows-scan",
    title="Which workflows are red on main right now, org-wide — the one-block scan",
    tags=["github", "ci", "actions", "org-wide", "digest"],
    surface="github",
    severity="medium",
    symptom="You need the latest-run-per-workflow on `main` for every active repo, filtered to failures, before deciding what to fix. (At the 2026-10-01 audit: 709 workflows scanned, 26 red across 20 repos.)",
    diagnose=r'''$ErrorActionPreference = "Continue"
$Out = Join-Path $env:USERPROFILE ("szl-red-" + (Get-Date -Format yyyyMMdd) + ".csv")
$Repos = gh repo list szl-holdings --limit 300 --json name,isArchived | ConvertFrom-Json | Where-Object { -not $_.isArchived }
$Rows = foreach ($r in $Repos) {
  $runs = gh run list --repo "szl-holdings/$($r.name)" --branch main --limit 40 --json workflowName,conclusion,createdAt,url,event 2>$null | ConvertFrom-Json
  $seen = @{}
  foreach ($run in $runs) {
    if ($seen.ContainsKey($run.workflowName)) { continue }; $seen[$run.workflowName] = 1
    if ($run.conclusion -in 'failure','timed_out','startup_failure','action_required') {
      [pscustomobject]@{ repo=$r.name; workflow=$run.workflowName; conclusion=$run.conclusion; event=$run.event; when=$run.createdAt.Substring(0,10); url=$run.url }
    }
  }
}
$Rows | Sort-Object repo, workflow | Tee-Object -Variable Red | Export-Csv -NoTypeInformation -LiteralPath $Out
$Red | Format-Table repo, workflow, conclusion, event, when -AutoSize
"red workflows: $(@($Red).Count)  ->  $Out"''',
    fix=r'''# For any row: pull the failing step lines
gh run view <databaseId-from-url> --repo szl-holdings/<repo> --log-failed 2>$null | Select-String "error|Error|Traceback|FAIL|401|400|404" | Select-Object -Last 20''',
    verify=r'''# Re-run the scan; the count should drop. Scheduled lanes (dead-man, constellation operator) re-evaluate on their own cadence.''',
    notes="Recurring classes seen 2026-10-01: HF deploy lanes failing on a missing/rotated HF_TOKEN (yarqa, szl-gpu-bridge, david-leads 401), Dependabot updater errors, estate schedulers failing closed on completeness, and the `.github` front-door validators after the profile rewrite. Each has its own entry here.",
    sources=["https://github.com/szl-holdings/.github/issues/158"],
)

add(
    id="gh-auth-and-rate-limit",
    title="gh says 401/403 or 'rate limit exceeded' — refresh auth, check scopes, wait honestly",
    tags=["github", "gh", "auth", "token", "rate-limit"],
    surface="local",
    severity="medium",
    symptom="`gh` calls fail with HTTP 401/403, `GraphQL: ... rate limit`, or `Resource not accessible by integration`.",
    diagnose=r'''gh auth status 2>&1 | Select-String "Logged in|Token scopes|error"
gh api rate_limit --jq '{core:.resources.core, graphql:.resources.graphql, search:.resources.search}' ''',
    fix=r'''# Re-authenticate interactively (browser), adding the scopes the org tooling uses
gh auth refresh -h github.com -s repo,workflow,read:org,admin:org,read:packages
# If a stale GH_TOKEN env var is shadowing your login:
if ($env:GH_TOKEN) { Remove-Item Env:GH_TOKEN }  # for this session only
# Rate-limited: wait until reset; do not spin retries
$Reset = gh api rate_limit --jq '.resources.core.reset'; [DateTimeOffset]::FromUnixTimeSeconds($Reset).LocalDateTime''',
    verify=r'''gh api user --jq .login; gh repo list szl-holdings --limit 1 --json name --jq '.[0].name' ''',
    notes="Org-admin actions (branch protection on 50+ repos, org secrets) need `admin:org`; a connector or app without it will report UNKNOWN, which is correct — do not read UNKNOWN as unprotected.",
    sources=["https://github.com/szl-holdings/szl-org-health/issues/176"],
)
