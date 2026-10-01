# OWNER-ONLY.ps1 - the fixes no agent can do remotely, in one paste (five parts, each skippable).
# Windows PowerShell 5.1, run as Administrator ON THE OWN-METAL BOX (omen tower or laptop), no prior shell state.
#   Part 1: bring the sovereign mesh back (cloudflared tunnel + Ollama + exporter) so gpu/gateway/meter/meter2 stop returning 530.
#   Part 2: re-seat the rotated Hugging Face token as the org-wide GitHub Actions secret and re-run the lanes that failed with 400/401.
#   Part 3: create the showcase.a-11-oy.com CNAME (Cloudflare connector token is broken) and enforce HTTPS on the Pages site.
#   Part 4: org ruleset protecting every default branch (needs admin:org on your login).
#   Part 5: resolve the vendored-source secret-scanning false positive after you see the evidence.
# Tokens are read with Read-Host -AsSecureString; nothing is echoed, logged, or committed. Press Enter at a prompt to skip that part.
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
foreach ($exe in "git","gh") { if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { throw "Required command '$exe' not found on PATH." } }
$Src = Join-Path $env:USERPROFILE "src"
if (-not (Test-Path -LiteralPath $Src -PathType Container)) { New-Item -ItemType Directory -Path $Src | Out-Null }
$A11oy = Join-Path $Src "a11oy"
$ErrorActionPreference = "Continue"
if (Test-Path -LiteralPath (Join-Path $A11oy ".git")) { git -C $A11oy pull --ff-only 2>&1 | Out-Null } else { gh repo clone szl-holdings/a11oy $A11oy -- --depth 1 2>&1 | Out-Null }
$ErrorActionPreference = "Stop"
$Mesh = Join-Path $A11oy "box-scripts\SZL_MESH_RESTART.ps1"
$Heal = Join-Path $A11oy "box-scripts\SZL_TUNNEL_HEAL.ps1"
if (-not (Test-Path -LiteralPath $Mesh -PathType Leaf)) { throw "Missing $Mesh - clone failed?" }

Write-Host ""; Write-Host "== PART 1 · sovereign mesh restart on $(hostname)" -ForegroundColor Cyan
$ErrorActionPreference = "Continue"
powershell -NoProfile -ExecutionPolicy Bypass -File $Mesh
$Down = @()
foreach ($h in "gateway","gpu","meter","meter2") {
    try { $c = (Invoke-WebRequest -UseBasicParsing -Method Head "https://$h.a-11-oy.com/" -TimeoutSec 10).StatusCode } catch { $c = $_.Exception.Response.StatusCode.value__ }
    if ("$c" -eq "530") { $Down += $h }
}
if ($Down.Count -gt 0 -and (Test-Path -LiteralPath $Heal -PathType Leaf)) {
    Write-Host ("still 530 after restart: " + ($Down -join ", ") + " -> running tunnel heal (re-routes CNAMEs to THIS tunnel)") -ForegroundColor Yellow
    powershell -NoProfile -ExecutionPolicy Bypass -File $Heal
}
$ErrorActionPreference = "Stop"
Write-Host ""; Write-Host "-- part 1 verify (200 up · 404/502/503 tunnel up, local service down · 530 tunnel not connected)" -ForegroundColor DarkGray
foreach ($h in "gateway","gpu","gpu2","meter","meter2") {
    try { $c = (Invoke-WebRequest -UseBasicParsing -Method Head "https://$h.a-11-oy.com/" -TimeoutSec 10).StatusCode } catch { $c = $_.Exception.Response.StatusCode.value__ }
    "{0,-8} {1}" -f $h, $c
}

Write-Host ""; Write-Host "== PART 2 · re-seat HF token for CI (org secret HF_TOKEN + alias HF_ORG_TOKEN)" -ForegroundColor Cyan
$Sec = Read-Host -AsSecureString "Paste the fresh fine-grained Hugging Face WRITE token (Enter to skip part 2)"
$Bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Sec)
$Tok = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($Bstr)
[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Bstr)
if ($Tok -and $Tok.Trim().Length -gt 0) {
    $ErrorActionPreference = "Continue"
    $Tok | gh secret set HF_TOKEN --org szl-holdings --visibility all
    $Tok | gh secret set HF_ORG_TOKEN --org szl-holdings --visibility all
    $ErrorActionPreference = "Stop"
    Remove-Variable Tok
    Write-Host "org secrets HF_TOKEN and HF_ORG_TOKEN set (names only are listed below; values are never shown)" -ForegroundColor Green
    gh secret list --org szl-holdings --json name,visibility --jq '.[]|"\(.name)  \(.visibility)"'
    Write-Host ""; Write-Host "-- re-running the lanes that failed with 400/401" -ForegroundColor DarkGray
    $ErrorActionPreference = "Continue"
    $Lanes = @(
        @{ repo = "szl-holdings/yarqa";          wf = "HF Space deploy" },
        @{ repo = "szl-holdings/szl-gpu-bridge";  wf = "Sync training-receipts card" },
        @{ repo = "szl-holdings/david-leads";     wf = "Deploy to HuggingFace Space" },
        @{ repo = "szl-holdings/puriq-live";      wf = "Publish PURIQ Hugging Face Space" },
        @{ repo = "szl-holdings/sda";             wf = "Deploy to Hugging Face Space" },
        @{ repo = "szl-holdings/szl-sovereign-os"; wf = "Hugging Face publication pipeline" }
    )
    foreach ($l in $Lanes) {
        $id = gh run list --repo $l.repo --workflow $l.wf --limit 1 --json databaseId --jq '.[0].databaseId' 2>$null
        if ($id) { gh run rerun $id --repo $l.repo --failed 2>$null | Out-Null; "rerun requested  {0}  {1}  run {2}" -f $l.repo, $l.wf, $id } else { "no run found     {0}  {1}" -f $l.repo, $l.wf }
    }
    $ErrorActionPreference = "Stop"
    Write-Host ""; Write-Host "verify in ~5 min:  gh run list --repo szl-holdings/yarqa --workflow 'HF Space deploy' --limit 1 --json conclusion" -ForegroundColor DarkGray
} else {
    Write-Host "part 2 skipped (no token entered)" -ForegroundColor Yellow
}

Write-Host ""; Write-Host "== PART 3 · showcase.a-11-oy.com DNS (one CNAME, DNS-only) + Pages HTTPS" -ForegroundColor Cyan
$CfSec = Read-Host -AsSecureString "Paste a Cloudflare API token with Zone:DNS:Edit on a-11-oy.com (Enter to skip part 3)"
$CfB = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($CfSec); $CfTok = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($CfB); [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($CfB)
if ($CfTok -and $CfTok.Trim().Length -gt 0) {
    $H = @{ Authorization = "Bearer $CfTok"; "Content-Type" = "application/json" }
    $Zone = "27911fb3d5ed874fdd4e844ed7f5e248"
    $Ver = Invoke-RestMethod -Headers $H "https://api.cloudflare.com/client/v4/user/tokens/verify"
    if ($Ver.result.status -ne "active") { throw "Cloudflare token is not active" }
    $Existing = (Invoke-RestMethod -Headers $H "https://api.cloudflare.com/client/v4/zones/$Zone/dns_records?name=showcase.a-11-oy.com").result
    if ($Existing.Count -eq 0) {
        $Body = '{"type":"CNAME","name":"showcase","content":"szl-holdings.github.io","ttl":1,"proxied":false}'
        $New = (Invoke-RestMethod -Method Post -Headers $H -Body $Body "https://api.cloudflare.com/client/v4/zones/$Zone/dns_records").result
        Write-Host ("created  {0} CNAME -> {1} proxied={2}" -f $New.name, $New.content, $New.proxied) -ForegroundColor Green
    } else { Write-Host ("exists   {0} -> {1}" -f $Existing[0].name, $Existing[0].content) -ForegroundColor Yellow }
    Remove-Variable CfTok, H
    Write-Host "waiting 90s for DNS, then asking GitHub Pages to enforce HTTPS (retry later if the certificate is still provisioning)" -ForegroundColor DarkGray
    Start-Sleep -Seconds 90
    $ErrorActionPreference = "Continue"
    gh api -X PUT repos/szl-holdings/szl-showcase/pages -F https_enforced=true 2>$null | Out-Null
    gh api repos/szl-holdings/szl-showcase/pages --jq '{status,cname,https_enforced}'
    $ErrorActionPreference = "Stop"
} else { Write-Host "part 3 skipped" -ForegroundColor Yellow }

Write-Host ""; Write-Host "== PART 4 · org rulesets: protect every default branch (needs admin:org on YOUR login)" -ForegroundColor Cyan
$Go = Read-Host "Create org ruleset 'szl-default-branch-integrity' (block deletion + force-push on every default branch)? type yes to proceed"
if ($Go -eq "yes") {
    $ErrorActionPreference = "Continue"
    gh auth refresh -h github.com -s admin:org,repo,workflow
    $Rules = @'
{ "name": "szl-default-branch-integrity", "target": "branch", "enforcement": "active",
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] },
                  "repository_name": { "include": ["~ALL"], "exclude": [], "protected": false } },
  "rules": [ { "type": "deletion" }, { "type": "non_fast_forward" } ],
  "bypass_actors": [ { "actor_id": 1, "actor_type": "OrganizationAdmin", "bypass_mode": "always" } ] }
'@
    $Rules | gh api -X POST orgs/szl-holdings/rulesets --input - --jq '{id,name,enforcement}'
    gh api orgs/szl-holdings/rulesets --jq '.[]|"\(.id) \(.name) \(.enforcement)"'
    $ErrorActionPreference = "Stop"
    Write-Host "This closes the 52-unprotected-default-branches finding (szl-org-health#176) for every current and future repo." -ForegroundColor Green
} else { Write-Host "part 4 skipped" -ForegroundColor Yellow }

Write-Host ""; Write-Host "== PART 5 · secret-scanning alert szl-forge#2 (Mistral pattern in vendored transformers source)" -ForegroundColor Cyan
gh api repos/szl-holdings/szl-forge/secret-scanning/alerts/2 --jq '{state,validity,secret_type_display_name}'
gh api repos/szl-holdings/szl-forge/secret-scanning/alerts/2/locations --jq '.[]|"\(.details.path):\(.details.start_line) @\(.details.commit_sha[0:10])"'
$Fp = Read-Host "Validity 'inactive' and paths inside .venv-*/site-packages/transformers/ confirm a false positive. Resolve it as false_positive? type yes"
if ($Fp -eq "yes") {
    gh api -X PATCH repos/szl-holdings/szl-forge/secret-scanning/alerts/2 -f state=resolved -f resolution=false_positive -f resolution_comment="Pattern match inside vendored transformers source in a since-removed committed venv (commit 7dfba5d8); validity inactive; path absent from HEAD. Audit 2026-10-01." --jq '{number,state,resolution}'
} else { Write-Host "part 5 skipped" -ForegroundColor Yellow }

Write-Host ""; Write-Host "done. david-leads also needs DAVID_DATASET_READ_TOKEN (read-only, dataset-scoped) as an environment secret in david-space-ci - see runbook entry hf-deploy-400-401-token." -ForegroundColor DarkGray
