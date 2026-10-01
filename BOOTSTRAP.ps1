# BOOTSTRAP.ps1 - get the private SZL ops runbook onto this box and make fixes one search away.
# Windows PowerShell 5.1, run as Administrator, no prior shell state required. ASCII only.
# Paste the whole block once. It: clones/updates the private repo, loads Find-Fix, opens the
# searchable site, and prints today's unblocker board. It merges nothing and writes nothing remote.
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$Src = Join-Path $env:USERPROFILE "src"
if (-not (Test-Path -LiteralPath $Src -PathType Container)) { New-Item -ItemType Directory -Path $Src | Out-Null }
$Root = Join-Path $Src "szl-ops-runbook"
foreach ($exe in "git","gh","python") { if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { throw "Required command '$exe' not found on PATH." } }
$ErrorActionPreference = "Continue"
if (Test-Path -LiteralPath (Join-Path $Root ".git")) {
    git -C $Root pull --ff-only 2>&1 | Out-Null
} else {
    gh repo clone szl-holdings/szl-ops-runbook $Root 2>&1 | Out-Null
}
$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath (Join-Path $Root "site\runbook.json") -PathType Leaf)) { throw "Clone failed or index missing: $Root\site\runbook.json" }
Set-Location -LiteralPath $Root
. (Join-Path $Root "tools\Find-Fix.ps1")
Start-Process (Join-Path $Root "site\index.html")
Write-Host ""
Write-Host "== runbook ready at $Root" -ForegroundColor Cyan
Write-Host "   Find-Fix 530        Find-Fix provenance -Show        Find-Fix 400 -Copy" -ForegroundColor DarkGray
Write-Host ""
$ErrorActionPreference = "Continue"
python (Join-Path $Root "tools\unblocker.py") --org szl-holdings --out (Join-Path $Root "board") 2>$null | Select-Object -First 40
$ErrorActionPreference = "Stop"
Write-Host ""
Write-Host ("board saved: " + (Join-Path $Root "board\latest.md")) -ForegroundColor Green
