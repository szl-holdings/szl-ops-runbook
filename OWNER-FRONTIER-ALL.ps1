& {
# =====================================================================================================
# SZL-FRONTIER-ALL-2026-10-01  -  one paste. Windows PowerShell 5.1, run as Administrator, no prior state.
# Wrapped in & { } so the whole block is parsed before anything runs: Read-Host prompts cannot swallow
# pasted lines, and nothing executes half-way. Nothing here force-pushes, deletes history, edits a
# receipt, or writes to Hugging Face. Every lane is isolated: a failure is recorded, the next lane runs.
#
# Lanes (toggle below):
#   1 Ollama      publish szlholdings/szl-khipu-1.5b from the verified kit in szl-serve (needs your account+key)
#   2 Docker Hub  install repo-scoped secrets on szl-holdings/registry-mirror, run the digest-verified mirror
#   3 Cloudflare  add the missing security headers on a-11-oy.com and a11oy.net via a Transform Rule
#   4 SECURITY.md open one PR per public repo lacking SECURITY.md (GitHub-verified server-side commits)
#   5 Heritage    request Software Heritage archival of the flagship repos (permanent SWHIDs)
#   6 Triage      port the two unique branches of your personal fork into the org repo, then archive the fork;
#                 read-only gate-12 preflight (no model run, no receipt edits)
#   7 a11oy       record your publisher-handoff decision on issue #2397 (the 8 a11oy PRs depend on it)
#   8 Tidy        delete the two superseded, PR-less hatun-mcp branches I left behind
#   9 Read-back   public probes; UI-only checklist; receipt JSON + transcript
# =====================================================================================================
$ErrorActionPreference = "Continue"      # native tools write to stderr; lanes throw explicitly where it matters
Set-StrictMode -Version 1.0
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ProgressPreference = "SilentlyContinue"
try { $OutputEncoding = New-Object System.Text.UTF8Encoding($false); [Console]::OutputEncoding = $OutputEncoding } catch { }

# ---------------- toggles ----------------
$DoOllama = $true; $DoDockerHub = $true; $DoCloudflare = $true; $DoSecurityWave = $true
$DoSoftwareHeritage = $true; $DoTriagePort = $true; $ArchivePersonalTriageFork = $true
$DoA11oyDecision = $true; $DoBranchTidy = $true

# ---------------- root, receipt, transcript ----------------
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Root  = Join-Path $env:USERPROFILE "szl-frontier"
New-Item -ItemType Directory -Force -Path $Root, (Join-Path $Root "receipts") | Out-Null
Set-Location -LiteralPath $Root
$Receipt = Join-Path $Root ("receipts\frontier-all-" + $Stamp + ".json")
Start-Transcript -LiteralPath (Join-Path $Root ("receipts\frontier-all-" + $Stamp + ".log")) | Out-Null
$R = [ordered]@{ ts = (Get-Date).ToUniversalTime().ToString("o"); host = $env:COMPUTERNAME; root = $Root; lanes = [ordered]@{} }

function Lane($n, $s, $d) {
  $R.lanes[$n] = [ordered]@{ state = $s; detail = ("" + $d); ts = (Get-Date).ToUniversalTime().ToString("o") }
  $c = "Cyan"; if ($s -match "FAIL|BLOCK|INCOMPLETE|SKIP") { $c = "Yellow" }; if ($s -match "MEASURED|^OK|DONE|PUBLISHED|LISTED|INSTALLED|ARCHIVED|OPENED|APPLIED|RECORDED") { $c = "Green" }
  Write-Host ("[{0}] {1}: {2}" -f $s, $n, $d) -ForegroundColor $c
}
function Save() { $R | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Receipt -Encoding UTF8 }
function Probe($url) { try { $r = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 30 -ErrorAction Stop; return [int]$r.StatusCode } catch { if ($_.Exception.Response) { return [int]$_.Exception.Response.StatusCode } else { return -1 } } }
function Hdr($resp, $name) { foreach ($k in $resp.Headers.Keys) { if ($k -ieq $name) { return ("" + $resp.Headers[$k]) } }; return "" }
function Invoke-Gh([string[]]$A) {   # gh with rate-limit backoff (your account's REST quota is shared with your other agents)
  $out = ""
  for ($i = 0; $i -lt 6; $i++) {
    $out = (& gh @A 2>&1 | Out-String); $code = $LASTEXITCODE
    if ($code -eq 0) { $global:GhExit = 0; return $out }
    if ($out -match "rate limit") { Write-Host ("   gh rate-limited; waiting 90s (try {0}/6)" -f ($i + 1)) -ForegroundColor DarkYellow; Start-Sleep -Seconds 90; continue }
    $global:GhExit = $code; return $out
  }
  $global:GhExit = 429; return $out
}
function Secret($prompt) {   # hidden input -> plain string in memory only; never written to disk or receipt
  $s = Read-Host $prompt -AsSecureString
  $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
  try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
}

# ---------------- preflight (read-only) ----------------
$HaveGh = [bool](Get-Command gh -ErrorAction SilentlyContinue)
$HaveGit = [bool](Get-Command git -ErrorAction SilentlyContinue)
$HaveOllama = [bool](Get-Command ollama -ErrorAction SilentlyContinue)
$GhOk = $false; if ($HaveGh) { & gh auth status 2>&1 | Out-Null; $GhOk = ($LASTEXITCODE -eq 0) }
$GhUser = ""; if ($GhOk) { $GhUser = (Invoke-Gh @("api", "user", "--jq", ".login")).Trim() }
$GitSign = ""; $GitKey = ""
if ($HaveGit) { $GitSign = (& git config --global --get commit.gpgsign 2>$null | Out-String).Trim(); $GitKey = (& git config --global --get user.signingkey 2>$null | Out-String).Trim() }
Lane "preflight" "OK" ("gh=$HaveGh auth=$GhOk user=$GhUser git=$HaveGit ollama=$HaveOllama commit.gpgsign='$GitSign' signingkey_set=" + [bool]$GitKey)
if ($HaveGit -and -not $GitKey) { Write-Host "   NOTE a11oy, killinchu, hatun-mcp, david-leads require VERIFIED commits on main. Your local git has no signing key." -ForegroundColor Yellow
  Write-Host "        SSH signing in 3 lines: git config --global gpg.format ssh ; git config --global user.signingkey `"$env:USERPROFILE\.ssh\id_ed25519.pub`" ; git config --global commit.gpgsign true  (then add the key as a Signing key at https://github.com/settings/keys)" -ForegroundColor Yellow }
Save

# ============================ LANE 1: Ollama ============================
if ($DoOllama) { try {
  if (-not $HaveOllama) { throw "ollama not installed (https://ollama.com/download/windows)" }
  $KitUrl = "https://raw.githubusercontent.com/szl-holdings/szl-serve/8c9c813f2cf747890fe9e61ef1e50c6ac994428b/ollama/Publish-Ollama.ps1"
  $KitSha = "f8af1af60c952f91e221386d7e079eba47e934c41ee5b1ee150be062471d62f4"
  $Kit = Join-Path $Root "Publish-Ollama.ps1"
  Invoke-WebRequest -UseBasicParsing -Uri $KitUrl -OutFile $Kit -TimeoutSec 120 -ErrorAction Stop
  $h = (Get-FileHash -Algorithm SHA256 -LiteralPath $Kit).Hash.ToLower()
  if ($h -ne $KitSha) { throw "kit hash mismatch $h (expected $KitSha); refusing to run an unverified script" }
  if ((Probe "https://ollama.com/szlholdings") -ne 200) {
    $KeyPub = Join-Path $env:USERPROFILE ".ollama\id_ed25519.pub"
    $PubKey = "(start the Ollama app once; it generates the key)"; if (Test-Path -LiteralPath $KeyPub) { $PubKey = (Get-Content -LiteralPath $KeyPub -Raw).Trim() }
    Lane "ollama" "SETUP_REQUIRED" ("1) create account 'szlholdings' at https://ollama.com/signup  2) add this key at https://ollama.com/settings/keys : " + $PubKey + "  3) rerun this block")
  } else {
    Unblock-File -LiteralPath $Kit
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Kit
    if ($LASTEXITCODE -eq 0) { Lane "ollama" "PUBLISHED_VERIFIED" "receipt in $env:USERPROFILE\szl-ollama\receipts ; paste OLLAMA_PAGE.md into https://ollama.com/szlholdings/szl-khipu-1.5b/edit" }
    else { Lane "ollama" "INCOMPLETE" "kit stopped before push (fail-closed); read $env:USERPROFILE\szl-ollama\receipts\*.log" }
  }
} catch { Lane "ollama" "FAILED" $_.Exception.Message } ; Save }

# ============================ LANE 2: Docker Hub mirror ============================
if ($DoDockerHub) { try {
  if (-not $GhOk) { throw "gh not authenticated (gh auth login)" }
  $existing = Invoke-Gh @("secret", "list", "--repo", "szl-holdings/registry-mirror")
  if ($existing -match "DOCKERHUB_TOKEN" -and $existing -match "DOCKERHUB_USERNAME") { Lane "dockerhub_secrets" "ALREADY_INSTALLED" "both secrets present on registry-mirror" }
  else {
    Write-Host "`nDocker Hub: create a Personal Access Token (Read & Write) at https://app.docker.com/settings/personal-access-tokens for the szlholdings org." -ForegroundColor Cyan
    $u = Read-Host "Docker Hub username (blank skips this lane)"
    if ([string]::IsNullOrWhiteSpace($u)) { throw "skipped by owner" }
    $null = Invoke-Gh @("secret", "set", "DOCKERHUB_USERNAME", "--repo", "szl-holdings/registry-mirror", "--body", $u)
    $tok = Secret "Docker Hub access token (hidden)"
    $null = Invoke-Gh @("secret", "set", "DOCKERHUB_TOKEN", "--repo", "szl-holdings/registry-mirror", "--body", $tok)
    $tok = $null
    if ($global:GhExit -ne 0) { throw "gh secret set DOCKERHUB_TOKEN failed" }
    Lane "dockerhub_secrets" "INSTALLED" "repository-scoped secrets set (values not recorded)"
  }
  $null = Invoke-Gh @("workflow", "run", "mirror-dockerhub.yml", "--repo", "szl-holdings/registry-mirror")
  Start-Sleep -Seconds 25
  $run = (Invoke-Gh @("run", "list", "--repo", "szl-holdings/registry-mirror", "--workflow", "mirror-dockerhub.yml", "--limit", "1", "--json", "url,status", "--jq", '.[0].url + " " + .[0].status')).Trim()
  Lane "dockerhub_mirror" "DISPATCHED" ($run + " ; receipt artifact proves each tag; https://hub.docker.com/u/szlholdings fills only after digest-verified copies")
} catch { Lane "dockerhub" "SKIPPED_OR_FAILED" $_.Exception.Message } ; Save }

# ============================ LANE 3: Cloudflare security headers ============================
# Audit 2026-09-30: a11oy.net lacks Content-Security-Policy and Referrer-Policy; neither domain sends
# Permissions-Policy or frame-ancestors. One Response Header Transform rule per zone, appended (never replacing
# existing rules). CSP is ADDED as a second header carrying only frame-ancestors, so an origin CSP is never overwritten.
if ($DoCloudflare) { try {
  Write-Host "`nCloudflare: create an API token at https://dash.cloudflare.com/profile/api-tokens with permissions Zone > Zone > Read and Zone > Transform Rules > Edit, scoped to a-11-oy.com and a11oy.net." -ForegroundColor Cyan
  $cf = Secret "Cloudflare API token (hidden; blank skips)"
  if ([string]::IsNullOrWhiteSpace($cf)) { throw "skipped by owner" }
  $H = @{ Authorization = "Bearer $cf"; "Content-Type" = "application/json" }
  $v = Invoke-RestMethod -Uri "https://api.cloudflare.com/client/v4/user/tokens/verify" -Headers $H -ErrorAction Stop
  if (-not $v.success) { throw "token did not verify" }
  $zones = [ordered]@{ "a-11-oy.com" = "27911fb3d5ed874fdd4e844ed7f5e248"; "a11oy.net" = "6893093cd089c9994349bc16b0906006" }
  $desc = "szl-security-headers-2026-10-01"
  $rule = @{ expression = "true"; description = $desc; action = "rewrite"; enabled = $true; action_parameters = @{ headers = @{
      "Referrer-Policy"         = @{ operation = "set"; value = "strict-origin-when-cross-origin" }
      "Permissions-Policy"      = @{ operation = "set"; value = "camera=(), microphone=(), geolocation=(), payment=(), usb=()" }
      "X-Content-Type-Options"  = @{ operation = "set"; value = "nosniff" }
      "Content-Security-Policy" = @{ operation = "add"; value = "frame-ancestors 'self'" } } } }
  $summary = @()
  foreach ($z in $zones.Keys) {
    $zid = $zones[$z]; $ep = "https://api.cloudflare.com/client/v4/zones/$zid/rulesets/phases/http_response_headers_transform/entrypoint"
    $cur = $null; try { $cur = Invoke-RestMethod -Uri $ep -Headers $H -ErrorAction Stop } catch { $cur = $null }
    $mode = ""
    if ($null -eq $cur -or -not $cur.success) {
      $null = Invoke-RestMethod -Method Put -Uri $ep -Headers $H -Body (@{ rules = @($rule) } | ConvertTo-Json -Depth 8) -ErrorAction Stop; $mode = "CREATED_ENTRYPOINT"
    } else {
      $rsId = $cur.result.id
      $match = @(); if ($cur.result.rules) { $match = @($cur.result.rules | Where-Object { $_.description -eq $desc }) }
      if ($match.Count -gt 0) { $null = Invoke-RestMethod -Method Patch -Uri "https://api.cloudflare.com/client/v4/zones/$zid/rulesets/$rsId/rules/$($match[0].id)" -Headers $H -Body ($rule | ConvertTo-Json -Depth 8) -ErrorAction Stop; $mode = "UPDATED_EXISTING_RULE" }
      else { $null = Invoke-RestMethod -Method Post -Uri "https://api.cloudflare.com/client/v4/zones/$zid/rulesets/$rsId/rules" -Headers $H -Body ($rule | ConvertTo-Json -Depth 8) -ErrorAction Stop; $mode = "APPENDED_RULE" }
    }
    Start-Sleep -Seconds 8
    $resp = Invoke-WebRequest -UseBasicParsing -Uri ("https://" + $z + "/") -TimeoutSec 30 -ErrorAction Stop
    $pp = Hdr $resp "Permissions-Policy"; $csp = Hdr $resp "Content-Security-Policy"; $rp = Hdr $resp "Referrer-Policy"
    $ok = ($pp.Length -gt 0) -and ($csp -match "frame-ancestors") -and ($rp.Length -gt 0)
    $summary += ("{0}: {1} readback={2} (Permissions-Policy={3}; frame-ancestors={4}; Referrer-Policy={5})" -f $z, $mode, $(if ($ok) { "MEASURED" } else { "NOT_YET_VISIBLE" }), [bool]$pp, ($csp -match "frame-ancestors"), [bool]$rp)
  }
  $cf = $null; $H = $null
  Lane "cloudflare_headers" "APPLIED" ($summary -join " | ")
} catch { Lane "cloudflare_headers" "SKIPPED_OR_FAILED" $_.Exception.Message } ; Save }

# ============================ LANE 4: SECURITY.md wave (Wave I) ============================
# Scorecard's Security-Policy check accepts the org-level file; the OpenSSF Best Practices form and humans do not.
# One GitHub-verified server-side commit per repo (createCommitOnBranch), one PR; your agents merge green PRs.
if ($DoSecurityWave) { try {
  if (-not $GhOk) { throw "gh not authenticated" }
  $secMd = "# Security policy`n`nReport vulnerabilities privately through GitHub Security Advisories on this repository`n(Security tab -> Report a vulnerability) or per the organization policy:`nhttps://github.com/szl-holdings/.github/blob/main/SECURITY.md`n`nPlease do not open public issues for undisclosed vulnerabilities.`n`nEvidence labels used in this repository (MEASURED / MODELED / DECLARED / SIMULATED / UNAVAILABLE / ROADMAP)`ndescribe what was observed; they are not security guarantees. Lambda remains Conjecture 1.`n"
  $secB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($secMd))
  $prBody = "Adds a repository-level SECURITY.md pointing to the organization policy.`n`nWhy: the OpenSSF Scorecard Security-Policy check accepts the org-level file, but the OpenSSF Best Practices badge form, GitHub's Security tab and human reviewers look for the file in the repository. Wave I, 2026-10-01.`n`nNo code, test, release or status change. Reversible by deleting one file. Lambda = Conjecture 1."
  $listJson = Invoke-Gh @("repo", "list", "szl-holdings", "--limit", "300", "--json", "name,isArchived,isPrivate,isFork,defaultBranchRef", "--jq", '[.[] | select(.isArchived==false and .isPrivate==false and .isFork==false) | {name:.name, branch:.defaultBranchRef.name}]')
  if ($global:GhExit -ne 0) { throw "repo list failed: $listJson" }
  $repos = @($listJson | ConvertFrom-Json)
  $opened = @(); $skipped = 0; $already = 0; $failed = @()
  foreach ($rp in $repos) {
    $name = $rp.name; $br = $rp.branch; if (-not $br) { $br = "main" }
    $has = $false
    foreach ($pth in @("SECURITY.md", ".github/SECURITY.md", "docs/SECURITY.md")) { $null = Invoke-Gh @("api", "repos/szl-holdings/$name/contents/$pth", "--jq", ".sha"); if ($global:GhExit -eq 0) { $has = $true; break } }
    if ($has) { $skipped++; continue }
    $openN = (Invoke-Gh @("pr", "list", "--repo", "szl-holdings/$name", "--head", "chore/security-policy", "--state", "open", "--json", "number", "--jq", "length")).Trim()
    if ($openN -ne "0" -and $openN -ne "") { $already++; continue }
    $sha = (Invoke-Gh @("api", "repos/szl-holdings/$name/git/ref/heads/$br", "--jq", ".object.sha")).Trim()
    if ($global:GhExit -ne 0 -or $sha.Length -ne 40) { $failed += "$name(ref)"; continue }
    $null = Invoke-Gh @("api", "-X", "POST", "repos/szl-holdings/$name/git/refs", "-f", "ref=refs/heads/chore/security-policy", "-f", "sha=$sha")   # 'already exists' is fine
    $bh = (Invoke-Gh @("api", "repos/szl-holdings/$name/git/ref/heads/chore/security-policy", "--jq", ".object.sha")).Trim()
    if ($global:GhExit -ne 0 -or $bh.Length -ne 40) { $failed += "$name(branch)"; continue }
    $null = Invoke-Gh @("api", "repos/szl-holdings/$name/contents/SECURITY.md?ref=chore/security-policy", "--jq", ".sha")
    if ($global:GhExit -ne 0) {
      $mut = @{ query = 'mutation($i: CreateCommitOnBranchInput!){ createCommitOnBranch(input:$i){ commit { oid } } }'
                variables = @{ i = @{ branch = @{ repositoryNameWithOwner = "szl-holdings/$name"; branchName = "chore/security-policy" }; expectedHeadOid = $bh
                                      message = @{ headline = "docs: add repository SECURITY.md (organization policy pointer)"; body = "Wave I, 2026-10-01. Server-side commit so signature-protected branches accept it. No code change." }
                                      fileChanges = @{ additions = @(@{ path = "SECURITY.md"; contents = $secB64 }) } } } } | ConvertTo-Json -Depth 10 -Compress
      $res = ($mut | & gh api graphql --input - 2>&1 | Out-String)
      if ($res -notmatch '"oid"') { $failed += "$name(commit)"; continue }
    }
    $pr = Invoke-Gh @("pr", "create", "--repo", "szl-holdings/$name", "--head", "chore/security-policy", "--base", $br, "--title", "docs: repository SECURITY.md (org policy pointer) - Wave I", "--body", $prBody)
    if ($global:GhExit -eq 0) { $opened += $name; Write-Host ("   opened " + $pr.Trim()) } else { $failed += "$name(pr)" }
  }
  Lane "security_md_wave" "OPENED" ("repos=" + $repos.Count + " already_had_file=" + $skipped + " pr_already_open=" + $already + " opened=" + $opened.Count + " failed=" + $failed.Count + $(if ($failed.Count) { " [" + ($failed -join ",") + "]" } else { "" }))
} catch { Lane "security_md_wave" "FAILED" $_.Exception.Message } ; Save }

# ============================ LANE 5: Software Heritage ============================
if ($DoSoftwareHeritage) { try {
  $swh = @()
  foreach ($r in @("a11oy", "killinchu", "hatun-mcp", "szl-forge", "platform", "lutar-lean", "szl-typesafe-triage", "szl-serve", "szl-receipt", "ci-witness-action")) {
    try { $res = Invoke-RestMethod -Method Post -Uri ("https://archive.softwareheritage.org/api/1/origin/save/git/url/https://github.com/szl-holdings/" + $r + "/") -TimeoutSec 60 -ErrorAction Stop
          $swh += ($r + "=" + $res.save_request_status) } catch { $swh += ($r + "=ERR") }
    Start-Sleep -Seconds 2
  }
  Lane "software_heritage" "REQUESTED" (($swh -join " ") + " ; status: https://archive.softwareheritage.org/save/list/")
} catch { Lane "software_heritage" "FAILED" $_.Exception.Message } ; Save }

# ============================ LANE 6: TypeSafe Triage fork port + gate-12 preflight ============================
if ($DoTriagePort) { try {
  if (-not ($GhOk -and $HaveGit)) { throw "needs gh auth + git" }
  $Tri = Join-Path $Root "szl-typesafe-triage"
  if (-not (Test-Path -LiteralPath (Join-Path $Tri ".git"))) { & git clone --quiet https://github.com/szl-holdings/szl-typesafe-triage.git $Tri; if ($LASTEXITCODE -ne 0) { throw "clone failed" } }
  Push-Location -LiteralPath $Tri
  try {
    & git remote get-url personal 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { & git remote add personal https://github.com/stephenlutar2-hash/szl-typesafe-triage.git }
    & git fetch --quiet origin; & git fetch --quiet personal
    if ($LASTEXITCODE -ne 0) { throw "fetch from personal fork failed (archived or renamed?)" }
    $ported = @(); $nothing = @()
    foreach ($b in @("eval-status-2026-09-28", "fix/card-generator-mojibake")) {
      $cnt = (& git rev-list --count ("origin/main..personal/" + $b) 2>$null | Out-String).Trim()
      if (-not $cnt -or $cnt -eq "0") { $nothing += $b; continue }
      & git push --quiet origin ("refs/remotes/personal/" + $b + ":refs/heads/port/" + $b)      # exact commits, nothing rewritten
      if ($LASTEXITCODE -ne 0) { throw "push of port/$b failed" }
      $draft = @(); if ($b -eq "eval-status-2026-09-28") { $draft = @("--draft") }
      $pr = Invoke-Gh (@("pr", "create", "--repo", "szl-holdings/szl-typesafe-triage", "--head", ("port/" + $b), "--base", "main", "--title", ("port: " + $b + " from personal fork (" + $cnt + " unique commits)"), "--body", ("Exact commits from stephenlutar2-hash/szl-typesafe-triage branch " + $b + ", ported so the personal fork can be archived. Review as the original PR would have been reviewed. Lambda = Conjecture 1.")) + $draft)
      if ($global:GhExit -eq 0) { $ported += ($b + " -> " + $pr.Trim()) } else { $ported += ($b + " -> PR_FAILED: " + $pr.Trim()) }
    }
    Lane "triage_port" "OPENED" ("ported: " + ($ported -join " ; ") + " | nothing_unique: " + ($nothing -join ","))
    if ($ArchivePersonalTriageFork -and (@($ported -match "PR_FAILED").Count -eq 0)) {
      $null = Invoke-Gh @("repo", "archive", "stephenlutar2-hash/szl-typesafe-triage", "--yes")
      if ($global:GhExit -eq 0) { Lane "triage_fork_archive" "ARCHIVED" "stephenlutar2-hash/szl-typesafe-triage (reversible: gh repo unarchive)" } else { Lane "triage_fork_archive" "FAILED" "gh repo archive failed" }
    }
    # gate-12 read-only preflight (files only; no model run; no receipt edits)
    $pf = @()
    foreach ($f in @("out\release_gate.json", "out\leakage_gate.json", "policies\redteam_probes.verified.jsonl", "PROMOTION_THRESHOLDS.json")) {
      $p = Join-Path $Tri $f
      if (Test-Path -LiteralPath $p -PathType Leaf) { $pf += ($f + "=" + (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.Substring(0, 12)) } else { $pf += ($f + "=absent") }
    }
    $lg = Join-Path $Tri "out\leakage_gate.json"
    if (Test-Path -LiteralPath $lg) { $j = Get-Content -LiteralPath $lg -Raw | ConvertFrom-Json; $pf += ("leakage.verdict=" + $j.verdict + " semantic_pass=" + $j.semantic_pass) }
    Lane "triage_gate12_preflight" "MEASURED" (($pf -join " ") + " | still 11/12 NOT_PROMOTABLE: red_team 10/42 false_label_on_refusal + leakage REFUSED. Next measured step = externally authored probe set (B7) + GPU semantic pass, receipts appended never edited.")
  } finally { Pop-Location }
} catch { Lane "triage_port" "FAILED" $_.Exception.Message } ; Save }

# ============================ LANE 7: a11oy publisher decision (issue #2397) ============================
if ($DoA11oyDecision) { try {
  if (-not $GhOk) { throw "gh not authenticated" }
  Write-Host "`na11oy canonical Space publisher is parked by design (manual_prerequisites() returns SETUP_REQUIRED/UNKNOWN unconditionally after #2383/#2384)." -ForegroundColor Cyan
  Write-Host " 1 = implement the verified handoff the code anticipates (verify_public_github_reader + cosign key self-check), then install A11OY_GITHUB_PUBLIC_READ_TOKEN and SZL_COSIGN_PRIVATE_PEM as Space secrets and re-run   [recommended]"
  Write-Host " 2 = receipted owner-approval flag consumed only by the canonical workflow"
  Write-Host " 3 = keep the hold; make the parity comparator continue-on-error for PRs only (deploy stays blocking)"
  $d = Read-Host "Your decision for https://github.com/szl-holdings/a11oy/issues/2397 (1/2/3, blank = decide later)"
  if ($d -in @("1", "2", "3")) {
    $opts = @{ "1" = "Option 1: implement the verified credential-authority handoff (verify_public_github_reader + cosign self-check), then install the two Space secrets and re-run the publisher."; "2" = "Option 2: receipted owner-approval flag (--owner-approved-handoff <signed-receipt>) consumed only by the canonical workflow."; "3" = "Option 3: keep the hold; parity comparator continue-on-error for pull requests only; deploy stays blocking." }
    $txt = $opts[$d]
    $null = Invoke-Gh @("issue", "comment", "2397", "--repo", "szl-holdings/a11oy", "--body", ("Owner decision (recorded from the frontier runbook, " + (Get-Date).ToUniversalTime().ToString("o") + "): " + $txt + " Agents may implement exactly this and nothing broader; the hold stays until the implementing PR is green and reviewed."))
    if ($global:GhExit -eq 0) { Lane "a11oy_publisher_decision" "RECORDED" $txt } else { Lane "a11oy_publisher_decision" "FAILED" "issue comment failed" }
  } else { Lane "a11oy_publisher_decision" "DEFERRED" "no option chosen; the 8 a11oy PRs stay red on 'Protected base matches immutable HF repository' until the publisher runs" }
} catch { Lane "a11oy_publisher_decision" "FAILED" $_.Exception.Message } ; Save }

# ============================ LANE 8: tidy my two superseded hatun-mcp branches ============================
if ($DoBranchTidy) { try {
  if (-not $GhOk) { throw "gh not authenticated" }
  $tidy = @()
  foreach ($b in @("fix/publish-mcp-sigpipe-1.0.1", "fix/publish-mcp-sigpipe-1.0.1-signed")) {
    $openN = (Invoke-Gh @("pr", "list", "--repo", "szl-holdings/hatun-mcp", "--head", $b, "--state", "open", "--json", "number", "--jq", "length")).Trim()
    if ($openN -ne "0" -and $openN -ne "") { $tidy += ($b + "=KEPT(open PR)"); continue }
    $null = Invoke-Gh @("api", "-X", "DELETE", ("repos/szl-holdings/hatun-mcp/git/refs/heads/" + $b))
    $tidy += ($b + $(if ($global:GhExit -eq 0) { "=DELETED" } else { "=NOT_FOUND_OR_FAILED" }))
  }
  Lane "branch_tidy" "DONE" ($tidy -join " ; ")
} catch { Lane "branch_tidy" "FAILED" $_.Exception.Message } ; Save }

# ============================ LANE 9: read-back probes ============================
$probes = [ordered]@{
  ollama_model_page   = "https://ollama.com/szlholdings/szl-khipu-1.5b"
  dockerhub_repos     = "https://hub.docker.com/v2/repositories/szlholdings/"
  mcp_registry_hatun  = "https://registry.modelcontextprotocol.io/v0/servers?search=io.github.szl-holdings/hatun-mcp"
  action_release      = "https://github.com/szl-holdings/ci-witness-action/releases/tag/v0.1.0"
  scorecard_a11oy     = "https://api.scorecard.dev/projects/github.com/szl-holdings/a11oy"
  scorecard_hatun     = "https://api.scorecard.dev/projects/github.com/szl-holdings/hatun-mcp"
  pypi_attest_sample  = "https://pypi.org/integrity/szl-nemo/0.4.1/szl_nemo-0.4.1.tar.gz/provenance"
  site_product        = "https://a-11-oy.com/"
  site_proof          = "https://a11oy.net/"
}
$pr2 = @(); foreach ($k in $probes.Keys) { $pr2 += ($k + "=" + (Probe $probes[$k])) }
try { $dh = Invoke-RestMethod -Uri "https://hub.docker.com/v2/repositories/szlholdings/?page_size=50" -TimeoutSec 30 -ErrorAction Stop; $pr2 += ("dockerhub_repo_count=" + $dh.count) } catch { }
try { $mcp = Invoke-RestMethod -Uri $probes.mcp_registry_hatun -TimeoutSec 30 -ErrorAction Stop; $pr2 += ("mcp_listed_versions=" + ((@($mcp.servers) | ForEach-Object { $_.server.version }) -join ",")) } catch { }
Lane "readback" "MEASURED" ($pr2 -join " ")

# ============================ UI-only checklist ============================
Write-Host "`nUI-only steps (cannot be scripted):" -ForegroundColor Cyan
Write-Host " A. GitHub Marketplace: https://github.com/szl-holdings/ci-witness-action/releases/edit/v0.1.0 -> tick 'Publish this Action to the GitHub Marketplace', accept the Developer Agreement, categories Continuous integration + Security, Update release."
Write-Host " B. Ollama page README: paste https://github.com/szl-holdings/szl-serve/blob/main/ollama/OLLAMA_PAGE.md into https://ollama.com/szlholdings/szl-khipu-1.5b/edit (after lane 1 is PUBLISHED_VERIFIED)."
Write-Host " C. PyPI organization: https://pypi.org/manage/organizations/ -> account name szl-holdings, display SZL Holdings, URL https://a-11-oy.com, type Company (USD 5 per member per month), size 2-5; submit from the PyPI account that owns the 18 szl-* projects."
Write-Host " D. OpenSSF Best Practices badge: https://www.bestpractices.dev/en/projects/new -> add https://github.com/szl-holdings/a11oy (answers: README, SECURITY.md, CONTRIBUTING.md, CI tests, CodeQL, HTTPS)."
Write-Host " E. LinkedIn: post Thursday 1 Oct 07:30-08:30 ET using 'LinkedIn post draft + timing (1 Oct 2026)' and the 9-slide carousel PDF as a document post; reply to every comment in the first hour; rewrite the About first line around governed AI and receipts."
Write-Host " F. a11oy Space secrets (only after option 1 lands): A11OY_GITHUB_PUBLIC_READ_TOKEN (fine-grained, public read) and SZL_COSIGN_PRIVATE_PEM at https://huggingface.co/spaces/SZLHOLDINGS/a11oy/settings ; then: gh workflow run 'Sync and Relock Canonical Hugging Face Space' --repo szl-holdings/a11oy --ref main"
Write-Host " G. Lean Reservoir: lutar-lean needs a top-level lake-manifest.json, an OSI license and 2+ GitHub stars; it is then indexed automatically."
Write-Host " H. arXiv: first submission needs an endorser in the category (cs.SE / cs.CR); candidates are the Type-Safe Triage (Zenodo 22888683) and GAR (Zenodo 22217725) manuscripts. HF Papers links models only via arXiv IDs."
Write-Host " I. platform/pyproject.toml still names the package repl-nix-workspace; rename before any registry sees it."
Write-Host " J. npm: claim the @szl-holdings scope (https://www.npmjs.com/org/create) before publishing a browser-side receipt verifier."

Save
Stop-Transcript | Out-Null
Write-Host ("`nReceipt: " + $Receipt) -ForegroundColor Cyan
$R.lanes.GetEnumerator() | ForEach-Object { Write-Host ("  {0,-26} {1}" -f $_.Key, $_.Value.state) }
}
