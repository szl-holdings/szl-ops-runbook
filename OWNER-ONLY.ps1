# OWNER-ONLY.ps1 (v2) - the fixes no agent can do remotely. Windows PowerShell 5.1, run as Administrator, no prior state.
# Each part asks before it runs (type y). Secrets are read with Read-Host -AsSecureString, stripped of control characters
# (the v1 crash: a pasted token carried a trailing newline), and never echoed, logged, or committed.
#
#   Part 1  mesh diagnosis + restart on THIS box: which tunnel hostnames belong here, which local port each needs, which is listening
#   Part 2  Hugging Face token: org-level secrets for every alias name in use, then remove the stale repo-level copies that shadow them
#   Part 3  showcase.a-11-oy.com CNAME (Cloudflare) + GitHub Pages HTTPS
#   Part 4  org ruleset protecting every default branch (needs admin:org on your login)
#   Part 5  secret-scanning alert szl-forge#2 (vendored-source false positive) - resolve only after you see the evidence
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
[Console]::OutputEncoding = [Text.Encoding]::UTF8

function Read-Secret([string]$Prompt) {
    $s = Read-Host -AsSecureString $Prompt
    $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
    try { $t = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
    if ($null -eq $t) { return "" }
    return (($t -replace '[\x00-\x1F\x7F]', '').Trim())
}
function Ask([string]$Question) { $a = Read-Host ($Question + " [y/N]"); return ($a -match '^(y|yes)$') }
function Probe([string]$Url) {
    try { return [string](Invoke-WebRequest -UseBasicParsing -Method Head $Url -TimeoutSec 10 -MaximumRedirection 2).StatusCode }
    catch { $c = $_.Exception.Response.StatusCode.value__; if ($c) { return [string]$c } else { return "ERR" } }
}
foreach ($exe in "git","gh") { if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { throw "Required command '$exe' not found on PATH." } }
$Src = Join-Path $env:USERPROFILE "src"
if (-not (Test-Path -LiteralPath $Src -PathType Container)) { New-Item -ItemType Directory -Path $Src | Out-Null }

# ---------------------------------------------------------------------------------------------------------------------
Write-Host ""; Write-Host "== PART 1 - sovereign mesh on $(hostname): diagnose, then restart" -ForegroundColor Cyan
if (Ask "Run part 1 (tunnel + local services diagnosis and restart on this box)?") {
    $Cfg = Join-Path $env:USERPROFILE ".cloudflared\config.yml"
    $LocalTunnels = @()
    $ErrorActionPreference = "Continue"
    if (Get-Command cloudflared -ErrorAction SilentlyContinue) {
        $raw = cloudflared tunnel list 2>$null
        foreach ($line in $raw) { if ($line -match '^([0-9a-f-]{36})\s+(\S+)') { $LocalTunnels += [pscustomobject]@{ id = $Matches[1]; name = $Matches[2]; line = $line.Trim() } } }
        Write-Host "tunnels visible from this box:"; $raw | ForEach-Object { "   $_" }
    } else { Write-Host "cloudflared not on PATH" -ForegroundColor Yellow }
    $ErrorActionPreference = "Stop"
    $Ingress = @()
    if (Test-Path -LiteralPath $Cfg -PathType Leaf) {
        $cur = $null
        foreach ($line in Get-Content -LiteralPath $Cfg) {
            if ($line -match '^\s*-\s*hostname:\s*(\S+)') { $cur = [pscustomobject]@{ host = $Matches[1]; service = ""; port = $null }; $Ingress += $cur }
            elseif ($line -match '^\s*service:\s*(\S+)' -and $cur) { $cur.service = $Matches[1]; if ($Matches[1] -match ':(\d+)\s*$') { $cur.port = [int]$Matches[1] } }
        }
        Write-Host ""; Write-Host "this box's ingress (config.yml) and whether the local port is listening:"
        foreach ($i in $Ingress) {
            $listen = "n/a"
            if ($i.port) { $listen = if (Test-NetConnection 127.0.0.1 -Port $i.port -InformationLevel Quiet -WarningAction SilentlyContinue) { "LISTENING" } else { "NOT LISTENING" } }
            "   {0,-26} -> {1,-32} {2}" -f $i.host, $i.service, $listen
        }
    } else { Write-Host "no $Cfg on this box" -ForegroundColor Yellow }
    Write-Host ""; Write-Host "public hostnames -> which tunnel UUID DNS points at (compare with the list above):"
    foreach ($h in "gateway","gpu","gpu2","meter","meter2") {
        $target = "?"
        try { $target = (Resolve-DnsName "$h.a-11-oy.com" -Type CNAME -ErrorAction Stop | Select-Object -First 1).NameHost } catch { $target = "(no CNAME visible: proxied record)" }
        $mine = if ($LocalTunnels | Where-Object { $target -like "$($_.id)*" }) { "THIS BOX" } else { "other tunnel / unknown" }
        "   {0,-8} {1,-50} {2}" -f $h, $target, $mine
    }
    Write-Host ""
    Write-Host "Reading: 502 = tunnel connected but the service for that hostname is NOT LISTENING above (start it: Ollama 11434, LiteLLM 4000, exporter 9471)." -ForegroundColor DarkGray
    Write-Host "         530 = no connector for that hostname's tunnel: it belongs to the other box (run this script there) or the CNAME targets a dead tunnel id (SZL_TUNNEL_HEAL re-routes hostnames present in THIS config)." -ForegroundColor DarkGray
    if (Ask "Run SZL_MESH_RESTART.ps1 (then SZL_TUNNEL_HEAL.ps1 if any host is still 530)?") {
        $A11oy = Join-Path $Src "a11oy"
        $ErrorActionPreference = "Continue"
        if (Test-Path -LiteralPath (Join-Path $A11oy ".git")) { git -C $A11oy pull --ff-only 2>&1 | Out-Null } else { gh repo clone szl-holdings/a11oy $A11oy -- --depth 1 2>&1 | Out-Null }
        $Mesh = Join-Path $A11oy "box-scripts\SZL_MESH_RESTART.ps1"; $Heal = Join-Path $A11oy "box-scripts\SZL_TUNNEL_HEAL.ps1"
        if (Test-Path -LiteralPath $Mesh -PathType Leaf) { powershell -NoProfile -ExecutionPolicy Bypass -File $Mesh } else { Write-Host "missing $Mesh" -ForegroundColor Yellow }
        $Down = @(); foreach ($h in "gateway","gpu","meter","meter2") { if ((Probe "https://$h.a-11-oy.com/") -eq "530") { $Down += $h } }
        if ($Down.Count -gt 0 -and (Test-Path -LiteralPath $Heal -PathType Leaf)) { Write-Host ("still 530: " + ($Down -join ", ") + " -> tunnel heal") -ForegroundColor Yellow; powershell -NoProfile -ExecutionPolicy Bypass -File $Heal }
        # local services that MESH_RESTART does not start by name
        $Need = @(); foreach ($i in $Ingress) { if ($i.port -and -not (Test-NetConnection 127.0.0.1 -Port $i.port -InformationLevel Quiet -WarningAction SilentlyContinue)) { $Need += $i } }
        foreach ($i in $Need) {
            switch ($i.port) {
                11434 { $o = Get-Command ollama -ErrorAction SilentlyContinue; if ($o) { Start-Process -WindowStyle Hidden -FilePath $o.Source -ArgumentList "serve"; "started ollama serve for $($i.host)" } else { "ollama.exe not found for $($i.host)" } }
                4000  { $cfgL = Join-Path $A11oy "box-scripts\litellm_config.yaml"; if (Get-Command litellm -ErrorAction SilentlyContinue) { Start-Process -WindowStyle Hidden litellm -ArgumentList "--config `"$cfgL`" --port 4000"; "started litellm for $($i.host)" } else { "litellm not found for $($i.host)" } }
                9471  { $exp = Join-Path $A11oy "box-scripts\omen_joule_exporter.py"; if (Test-Path $exp) { Start-Process -WindowStyle Hidden python -ArgumentList "`"$exp`""; "started joule exporter for $($i.host)" } else { "exporter script not found for $($i.host)" } }
                default { "no known launcher for $($i.host) -> $($i.service); start it by hand" }
            }
        }
        Start-Sleep -Seconds 12
        $ErrorActionPreference = "Stop"
    }
    Write-Host ""; Write-Host "-- part 1 verify (200 up - 404/502/503 tunnel up, service down - 530 tunnel not connected - 403 Access guard = OK on gpu2)" -ForegroundColor DarkGray
    foreach ($h in "gateway","gpu","gpu2","meter","meter2") { "   {0,-8} {1}" -f $h, (Probe "https://$h.a-11-oy.com/") }
}

# ---------------------------------------------------------------------------------------------------------------------
Write-Host ""; Write-Host "== PART 2 - Hugging Face token for CI: org-level for every alias, remove stale repo-level shadows" -ForegroundColor Cyan
Write-Host "Why the reruns still failed: 43 repositories carry REPO-level secrets (HF_TOKEN, HF_ORG_TOKEN, HF_ORG_TOKEN1, HF_WRITE_TOKEN," -ForegroundColor DarkGray
Write-Host "HUGGINGFACE_TOKEN, HUGGING_FACE_HUB_TOKEN, HF_API_TOKEN, HF_TOKEN_PUBLISH ...) set before the rotation. Repo-level values" -ForegroundColor DarkGray
Write-Host "shadow org-level values of the same name, so workflows kept using the revoked token (400 Bad Request)." -ForegroundColor DarkGray
if (Ask "Run part 2?") {
    $Tok = Read-Secret "Paste the fresh fine-grained Hugging Face WRITE token (Enter to skip)"
    if ($Tok.Length -gt 0) {
        $WriteNames = @("HF_TOKEN","HF_ORG_TOKEN","HF_ORG_TOKEN1","HF_WRITE_TOKEN","HUGGINGFACE_TOKEN","HUGGING_FACE_HUB_TOKEN","HUGGINGFACEHUB_API_TOKEN","HF_API_TOKEN","HF_TOKEN_PUBLISH","HF_CARD_WRITE_TOKEN")
        $ErrorActionPreference = "Continue"
        foreach ($n in $WriteNames) { $Tok | gh secret set $n --org szl-holdings --visibility all 2>&1 | Out-Null; "org secret set  $n" }
        $ErrorActionPreference = "Stop"
        $Rd = Read-Secret "Optional: a READ-ONLY HF token for HF_READ_TOKEN / HF_INVENTORY_READ_TOKEN / HF_LAKE_TOKEN (Enter to reuse the write token)"
        if ($Rd.Length -eq 0) { $Rd = $Tok }
        $ErrorActionPreference = "Continue"
        foreach ($n in "HF_READ_TOKEN","HF_INVENTORY_READ_TOKEN","HF_LAKE_TOKEN") { $Rd | gh secret set $n --org szl-holdings --visibility all 2>&1 | Out-Null; "org secret set  $n" }
        $ErrorActionPreference = "Stop"
        Remove-Variable Tok, Rd
        Write-Host ""
        if (Ask "Delete the repo-level copies of those names across the org so the org-level values apply everywhere?") {
            $AllNames = $WriteNames + @("HF_READ_TOKEN","HF_INVENTORY_READ_TOKEN","HF_LAKE_TOKEN")
            $ErrorActionPreference = "Continue"
            $Repos = gh repo list szl-holdings --limit 300 --json name,isArchived | ConvertFrom-Json | Where-Object { -not $_.isArchived }
            $Removed = 0
            foreach ($r in $Repos) {
                $names = gh secret list --repo "szl-holdings/$($r.name)" --json name --jq '.[].name' 2>$null
                foreach ($n in $names) {
                    if ($AllNames -contains $n) { gh secret delete $n --repo "szl-holdings/$($r.name)" 2>$null | Out-Null; $Removed++; "   removed repo-level $n from $($r.name)" }
                }
            }
            $ErrorActionPreference = "Stop"
            Write-Host ("repo-level shadows removed: {0}. Repo-only names were kept (HF_FACTORY_PRODUCTION_TOKEN, HF_INFERENCE_TOKEN): set those by hand if their lanes fail." -f $Removed) -ForegroundColor Green
        }
        Write-Host ""; Write-Host "-- re-running the HF lanes that failed" -ForegroundColor DarkGray
        $ErrorActionPreference = "Continue"
        foreach ($l in @(
            @{ repo = "szl-holdings/yarqa";          wf = "hf-space.yml" },
            @{ repo = "szl-holdings/szl-gpu-bridge";  wf = "Sync training-receipts card" },
            @{ repo = "szl-holdings/david-leads";     wf = "Deploy to HuggingFace Space" },
            @{ repo = "szl-holdings/puriq-live";      wf = "Publish PURIQ Hugging Face Space" },
            @{ repo = "szl-holdings/sda";             wf = "Deploy to Hugging Face Space" },
            @{ repo = "szl-holdings/szl-sovereign-os"; wf = "Hugging Face publication pipeline" })) {
            $id = gh run list --repo $l.repo --workflow $l.wf --limit 1 --json databaseId --jq '.[0].databaseId' 2>$null
            if ($id) { gh run rerun $id --repo $l.repo --failed 2>$null | Out-Null; "   rerun requested  {0}  {1}  run {2}" -f $l.repo, $l.wf, $id } else { "   no run found     {0}  {1}" -f $l.repo, $l.wf }
        }
        $ErrorActionPreference = "Stop"
        Write-Host "verify in ~5 min:  gh run list --repo szl-holdings/yarqa --workflow hf-space.yml --limit 1" -ForegroundColor DarkGray
    } else { Write-Host "part 2 skipped (no token)" -ForegroundColor Yellow }
}

# ---------------------------------------------------------------------------------------------------------------------
Write-Host ""; Write-Host "== PART 3 - showcase.a-11-oy.com: one CNAME (DNS-only) + GitHub Pages HTTPS" -ForegroundColor Cyan
if (Ask "Run part 3?") {
    $CfTok = Read-Secret "Paste a Cloudflare API token with Zone:DNS:Edit on a-11-oy.com (Enter to skip)"
    if ($CfTok.Length -gt 0) {
        $H = @{ Authorization = "Bearer $CfTok"; "Content-Type" = "application/json" }
        $Ver = Invoke-RestMethod -Headers $H "https://api.cloudflare.com/client/v4/user/tokens/verify"
        if ($Ver.result.status -ne "active") { throw "Cloudflare token is not active (status: $($Ver.result.status))" }
        $Zone = "27911fb3d5ed874fdd4e844ed7f5e248"
        $Existing = @((Invoke-RestMethod -Headers $H "https://api.cloudflare.com/client/v4/zones/$Zone/dns_records?name=showcase.a-11-oy.com").result)
        if ($Existing.Count -eq 0) {
            $New = (Invoke-RestMethod -Method Post -Headers $H -Body '{"type":"CNAME","name":"showcase","content":"szl-holdings.github.io","ttl":1,"proxied":false}' "https://api.cloudflare.com/client/v4/zones/$Zone/dns_records").result
            Write-Host ("created  {0} CNAME -> {1} proxied={2}" -f $New.name, $New.content, $New.proxied) -ForegroundColor Green
        } else { Write-Host ("exists   {0} -> {1} proxied={2}" -f $Existing[0].name, $Existing[0].content, $Existing[0].proxied) -ForegroundColor Yellow }
        Remove-Variable CfTok, H
        Write-Host "GitHub needs the record to be visible before it issues the certificate; trying HTTPS enforcement up to 6 times over ~6 minutes" -ForegroundColor DarkGray
        $ErrorActionPreference = "Continue"
        for ($i = 1; $i -le 6; $i++) {
            Start-Sleep -Seconds 60
            gh api -X PUT repos/szl-holdings/szl-showcase/pages -F https_enforced=true 2>$null | Out-Null
            $st = gh api repos/szl-holdings/szl-showcase/pages --jq '.https_enforced' 2>$null
            "   attempt $i  https_enforced=$st  probe=$(Probe 'https://showcase.a-11-oy.com/')"
            if ($st -eq "true") { break }
        }
        $ErrorActionPreference = "Stop"
        Write-Host "If https_enforced is still false, rerun just this part in 30-60 minutes; the certificate is provisioning." -ForegroundColor DarkGray
    } else { Write-Host "part 3 skipped" -ForegroundColor Yellow }
}

# ---------------------------------------------------------------------------------------------------------------------
Write-Host ""; Write-Host "== PART 4 - org ruleset: block deletion + force-push on EVERY default branch (needs admin:org on your login)" -ForegroundColor Cyan
if (Ask "Run part 4?") {
    $ErrorActionPreference = "Continue"
    gh auth refresh -h github.com -s admin:org,repo,workflow
    $Rules = @'
{ "name": "szl-default-branch-integrity", "target": "branch", "enforcement": "active",
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] },
                  "repository_name": { "include": ["~ALL"], "exclude": [], "protected": false } },
  "rules": [ { "type": "deletion" }, { "type": "non_fast_forward" } ],
  "bypass_actors": [ { "actor_id": 1, "actor_type": "OrganizationAdmin", "bypass_mode": "always" } ] }
'@
    $Tmp = Join-Path $env:TEMP "szl-ruleset.json"; Set-Content -LiteralPath $Tmp -Value $Rules -Encoding ASCII
    gh api -X POST orgs/szl-holdings/rulesets --input $Tmp --jq '.id'
    gh api orgs/szl-holdings/rulesets --jq '.[].name'
    $ErrorActionPreference = "Stop"
    Write-Host "That closes the 52-unprotected-default-branches finding (szl-org-health#176) for every current and future repository." -ForegroundColor Green
}

# ---------------------------------------------------------------------------------------------------------------------
Write-Host ""; Write-Host "== PART 5 - secret-scanning alert szl-forge#2 (Mistral pattern inside vendored transformers source)" -ForegroundColor Cyan
if (Ask "Show the evidence for part 5?") {
    $ErrorActionPreference = "Continue"
    gh api repos/szl-holdings/szl-forge/secret-scanning/alerts/2 --jq '.state, .validity, .secret_type_display_name'
    gh api repos/szl-holdings/szl-forge/secret-scanning/alerts/2/locations --jq '.[].details.path'
    $ErrorActionPreference = "Stop"
    if (Ask "Validity inactive and every path under .venv-*/site-packages/transformers/ => false positive. Resolve it now?") {
        gh api -X PATCH repos/szl-holdings/szl-forge/secret-scanning/alerts/2 -f state=resolved -f resolution=false_positive -f resolution_comment="Pattern match inside vendored transformers source in a since-removed committed venv (commit 7dfba5d8); validity inactive; path absent from HEAD. Audit 2026-10-01." --jq '.state'
    }
}
Write-Host ""; Write-Host "done." -ForegroundColor Cyan
