& {
# HF-ROTATE.ps1 - finish a Hugging Face token rotation from $env:HF_TOKEN (set it first via Get-Credential, never Read-Host in a paste).
# Windows PowerShell 5.1, Administrator. Replaces HF_TOKEN only where one already exists. Prints no secret values.
$ErrorActionPreference = "Continue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$T = $env:HF_TOKEN
if (-not $T -or $T -notmatch '^hf_[A-Za-z0-9]{30,}$') { Write-Host "No verified token in `$env:HF_TOKEN - set it first." -ForegroundColor Red; return }
$Spaces = @("SZLHOLDINGS/david-leads")          # add other Spaces that hold an HF_TOKEN secret, one per entry
$Out = Join-Path $env:USERPROFILE ("szl-frontier\receipts\hf-rotation-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".json")
New-Item -ItemType Directory -Force -Path (Split-Path $Out) | Out-Null
$R = [ordered]@{ ts = (Get-Date).ToUniversalTime().ToString("o"); steps = @() }
function Step($n, $s, $d) { $R.steps += [ordered]@{ step = $n; state = $s; detail = ("" + $d) }; $c = "Cyan"; if ($s -match "OK|DONE|ROTATED|RUNNING|LIVE") { $c = "Green" }; if ($s -match "FAIL|SKIP|ERR") { $c = "Yellow" }; Write-Host ("[{0}] {1}: {2}" -f $s, $n, $d) -ForegroundColor $c }
function Gh2([string[]]$A) { for ($i = 0; $i -lt 6; $i++) { $o = (& gh @A 2>&1 | Out-String); if ($LASTEXITCODE -eq 0) { $global:GhExit = 0; return $o }; if ($o -match "rate limit") { Start-Sleep -Seconds 90; continue }; $global:GhExit = $LASTEXITCODE; return $o }; $global:GhExit = 429; return "" }
$H = @{ Authorization = "Bearer $T"; "Content-Type" = "application/json" }

# 1) prove the token once more and bind identity into the receipt
$who = Invoke-RestMethod -Uri "https://huggingface.co/api/whoami-v2" -Headers $H
Step "whoami" "OK" ("user=" + $who.name + " role=" + $who.auth.accessToken.role)

# 2) Hugging Face Space secrets -> upsert HF_TOKEN, restart, wait for RUNNING
foreach ($sp in $Spaces) {
  try {
    $body = @{ key = "HF_TOKEN"; value = $T; description = ("rotated " + (Get-Date).ToUniversalTime().ToString("o")) } | ConvertTo-Json
    $null = Invoke-RestMethod -Method Post -Uri ("https://huggingface.co/api/spaces/" + $sp + "/secrets") -Headers $H -Body $body -ErrorAction Stop
    $null = Invoke-RestMethod -Method Post -Uri ("https://huggingface.co/api/spaces/" + $sp + "/restart") -Headers $H -ErrorAction Stop
    $stage = ""; for ($i = 0; $i -lt 24; $i++) { Start-Sleep -Seconds 10; try { $stage = (Invoke-RestMethod -Uri ("https://huggingface.co/api/spaces/" + $sp + "/runtime") -Headers $H -ErrorAction Stop).stage } catch { $stage = "?" }; if ($stage -eq "RUNNING") { break } }
    Step ("space " + $sp) $(if ($stage -eq "RUNNING") { "ROTATED_RUNNING" } else { "ROTATED_STAGE_" + $stage }) "secret upserted, Space restarted"
  } catch { Step ("space " + $sp) "FAILED" $_.Exception.Message }
}
try {
  $lanes = Invoke-RestMethod -Uri "https://szlholdings-david-leads.hf.space/api/frontier-desk" -TimeoutSec 60 -ErrorAction Stop
  $live = @($lanes.sources | Where-Object { $_.mode -eq "LIVE" }).Count
  Step "david-leads lanes" $(if ($live -ge 4) { "LIVE_" + $live } else { "LIVE_" + $live + "_recheck_in_2min" }) ($live.ToString() + " of " + @($lanes.sources).Count + " LIVE")
} catch { Step "david-leads lanes" "NOT_READY" "frontier-desk not answering yet; re-check in 2 min" }

# 3) GitHub Actions secrets named HF_TOKEN: org level (visibility preserved) + every repo that has one
& gh auth status 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { Step "github" "SKIP" "gh not authenticated" } else {
  $orgSec = Gh2 @("api", "orgs/szl-holdings/actions/secrets/HF_TOKEN")
  if ($global:GhExit -eq 0) {
    $vis = ($orgSec | ConvertFrom-Json).visibility
    if ($vis -eq "selected") { $sel = (Gh2 @("api", "orgs/szl-holdings/actions/secrets/HF_TOKEN/repositories", "--jq", '[.repositories[].name] | join(",")')).Trim(); $null = Gh2 @("secret", "set", "HF_TOKEN", "--org", "szl-holdings", "--visibility", "selected", "--repos", $sel, "--body", $T) }
    else { $null = Gh2 @("secret", "set", "HF_TOKEN", "--org", "szl-holdings", "--visibility", $vis, "--body", $T) }
    Step "org secret HF_TOKEN" $(if ($global:GhExit -eq 0) { "ROTATED" } else { "FAILED" }) ("visibility=" + $vis)
  } else { Step "org secret HF_TOKEN" "ABSENT" "no org-level HF_TOKEN" }
  $repos = @((Gh2 @("repo", "list", "szl-holdings", "--limit", "300", "--json", "name,isArchived", "--jq", '[.[] | select(.isArchived==false) | .name] | sort')) | ConvertFrom-Json)
  $rotated = @(); $failed = @()
  foreach ($r in $repos) {
    $lst = Gh2 @("secret", "list", "--repo", ("szl-holdings/" + $r))
    if ($global:GhExit -ne 0 -or $lst -notmatch "(?m)^HF_TOKEN\s") { continue }
    $null = Gh2 @("secret", "set", "HF_TOKEN", "--repo", ("szl-holdings/" + $r), "--body", $T)
    if ($global:GhExit -eq 0) { $rotated += $r } else { $failed += $r }
  }
  Step "repo secrets HF_TOKEN" "ROTATED" ("repos scanned=" + $repos.Count + " rotated=" + $rotated.Count + " [" + ($rotated -join ",") + "] failed=" + ($failed -join ","))
}

# 4) local machine: HF CLI token file, persisted HF_TOKEN env vars, cached git credential for huggingface.co
$tokFile = Join-Path $env:USERPROFILE ".cache\huggingface\token"
if (Test-Path -LiteralPath $tokFile) { [IO.File]::WriteAllText($tokFile, $T); Step "hf cli token file" "ROTATED" $tokFile } else { Step "hf cli token file" "ABSENT" $tokFile }
foreach ($scope in @("User", "Machine")) { $cur = [Environment]::GetEnvironmentVariable("HF_TOKEN", $scope); if ($cur -and $cur -ne $T) { try { [Environment]::SetEnvironmentVariable("HF_TOKEN", $T, $scope); Step ("env HF_TOKEN " + $scope) "ROTATED" "persisted variable replaced" } catch { Step ("env HF_TOKEN " + $scope) "FAILED" $_.Exception.Message } } }
if (Get-Command git -ErrorAction SilentlyContinue) { "url=https://huggingface.co`n" | & git credential reject 2>$null; Step "git credential huggingface.co" "CLEARED" "next git push to the Hub will ask for the new token" }

$R | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $Out -Encoding UTF8
Write-Host ("`nReceipt (no secret values): " + $Out) -ForegroundColor Cyan
$T = $null; $H = $null
}
