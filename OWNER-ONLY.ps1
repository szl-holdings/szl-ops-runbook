# OWNER-ONLY.ps1 - the two fixes no agent can do remotely, in one paste.
# Windows PowerShell 5.1, run as Administrator ON THE OWN-METAL BOX (omen tower or laptop), no prior shell state.
#   Part 1: bring the sovereign mesh back (cloudflared tunnel + Ollama + exporter) so gpu/gateway/meter/meter2 stop returning 530.
#   Part 2: re-seat the rotated Hugging Face token as the org-wide GitHub Actions secret and re-run the lanes that failed with 400/401.
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
Write-Host ""; Write-Host "done. david-leads also needs DAVID_DATASET_READ_TOKEN (read-only, dataset-scoped) as an environment secret in david-space-ci - see runbook entry hf-deploy-400-401-token." -ForegroundColor DarkGray
