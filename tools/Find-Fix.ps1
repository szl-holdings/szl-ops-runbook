# Find-Fix.ps1 - search the SZL ops runbook from the terminal and print the fix block.
# Windows PowerShell 5.1 safe. ASCII only.
#
#   . .\tools\Find-Fix.ps1            # dot-source once per session
#   Find-Fix 530                      # list matches for a symptom
#   Find-Fix "400 Bad Request" -Show  # print symptom + diagnose + fix + verify of the best match
#   Find-Fix provenance -Copy         # copy the best match's FIX block to the clipboard
#
function Find-Fix {
    [CmdletBinding()]
    param(
        [Parameter(Position = 0, ValueFromRemainingArguments = $true)] [string[]] $Terms,
        [switch] $Show,
        [switch] $Copy,
        [string] $IndexPath
    )
    if (-not $IndexPath) {
        $here = Split-Path -Parent $MyInvocation.MyCommand.Path
        $IndexPath = Join-Path (Split-Path -Parent $here) "site\runbook.json"
    }
    if (-not (Test-Path -LiteralPath $IndexPath -PathType Leaf)) { throw "runbook index not found: $IndexPath (run: python tools\build.py)" }
    $data = Get-Content -LiteralPath $IndexPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $q = @($Terms | ForEach-Object { $_.ToLowerInvariant() } | Where-Object { $_ })
    $rows = foreach ($e in $data.entries) {
        $hay = (@($e.id, $e.title, $e.symptom, ($e.tags -join " "), $e.notes, $e.diagnose, $e.fix) -join "`n").ToLowerInvariant()
        $score = 0; $miss = $false
        foreach ($t in $q) {
            if ($hay.IndexOf($t) -lt 0) { $miss = $true; break }
            $score += 1
            if ($e.title.ToLowerInvariant().IndexOf($t) -ge 0) { $score += 5 }
            if ($e.id.ToLowerInvariant().IndexOf($t) -ge 0) { $score += 4 }
            if (($e.tags -join " ").ToLowerInvariant().IndexOf($t) -ge 0) { $score += 3 }
        }
        if (-not $miss) { [pscustomobject]@{ score = $score; id = $e.id; surface = $e.surface; severity = $e.severity; title = $e.title; entry = $e } }
    }
    $rows = @($rows | Sort-Object score -Descending, title)
    if ($rows.Count -eq 0) { Write-Host "no match. try a symptom word: 530, 400, BEHIND, provenance, CONFIG_ERROR, stale" -ForegroundColor Yellow; return }
    if (-not $Show -and -not $Copy) {
        $rows | Select-Object id, surface, severity, title | Format-Table -AutoSize
        Write-Host ("{0} match(es). Add -Show to print the best one, -Copy to put its fix on the clipboard." -f $rows.Count) -ForegroundColor DarkGray
        return
    }
    $e = $rows[0].entry
    if ($Copy) { Set-Clipboard -Value $e.fix; Write-Host ("copied FIX block of '{0}' to clipboard" -f $e.id) -ForegroundColor Green }
    if ($Show -or -not $Copy) {
        Write-Host ""; Write-Host ("== {0}  [{1} / {2}]" -f $e.title, $e.surface, $e.severity) -ForegroundColor Cyan
        Write-Host ("id: {0}   last verified: {1}" -f $e.id, $e.last_verified) -ForegroundColor DarkGray
        Write-Host ""; Write-Host "SYMPTOM" -ForegroundColor Yellow; Write-Host $e.symptom
        Write-Host ""; Write-Host "DIAGNOSE" -ForegroundColor Yellow; Write-Host $e.diagnose
        Write-Host ""; Write-Host "FIX" -ForegroundColor Yellow; Write-Host $e.fix
        Write-Host ""; Write-Host "VERIFY" -ForegroundColor Yellow; Write-Host $e.verify
        Write-Host ""; Write-Host "NOTES" -ForegroundColor Yellow; Write-Host $e.notes
        if ($e.sources) { Write-Host ""; Write-Host "SOURCES" -ForegroundColor Yellow; $e.sources | ForEach-Object { Write-Host ("  " + $_) } }
    }
}
Write-Host "Find-Fix loaded. Try:  Find-Fix 530   |   Find-Fix provenance -Show   |   Find-Fix 400 -Copy" -ForegroundColor DarkGray
