---
id: ps51-gotchas
title: "Windows PowerShell 5.1 gotchas that have eaten whole sessions"
surface: local
severity: medium
tags: [powershell, windows, local, paste, encoding]
last_verified: 2026-10-01
---
# Windows PowerShell 5.1 gotchas that have eaten whole sessions

## Symptom
A pasted block hangs at `>>`, aborts on the first native stderr line, mangles em-dashes/arrows, refuses to run a downloaded .ps1, or a 25 KB paste silently truncates.

## Diagnose (PowerShell 5.1)
```powershell
$PSVersionTable.PSVersion
Get-ExecutionPolicy -List
[Console]::OutputEncoding.WebName; $OutputEncoding.WebName
```

## Fix
```powershell
# 1. '>>' prompt = unfinished construct. Ctrl+C until you see 'PS ...>' again, then paste ONE complete unit (no copied prompt markers).
# 2. Native stderr under Stop aborts the script (gh/git/python write progress to stderr). Wrap native calls:
function Invoke-Native { param([string]$Exe, [string[]]$Args) $o = & $Exe @Args 2>&1; if ($LASTEXITCODE -ne 0) { throw "$Exe exited $LASTEXITCODE`n$($o -join "`n")" }; $o }
#    or run with  $ErrorActionPreference = "Continue"  around gh/git and test $LASTEXITCODE yourself.
# 3. Save scripts ASCII-only or UTF-8 WITH BOM; 5.1 misreads BOM-less UTF-8 (box-scripts are ASCII on purpose).
Set-Content -LiteralPath .\x.ps1 -Value $Text -Encoding UTF8   # 5.1's UTF8 writes a BOM
# 4. Downloaded file: unblock, then run with a clean host
Unblock-File .\szl-handle-all.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\szl-handle-all.ps1
# 5. Long payloads: ship a .ps1 file + 2-line launcher instead of a 300-line paste (the Chaski gate JSON hand-paste broke this way).
# 6. Relative paths resolve against the child process cwd — always Resolve-Path and pass absolute paths to python/gh.
```

## Verify
```powershell
# A clean unit ends at a normal prompt with the final line printed by your script, not by the host.
```

## Notes
Prefer `powershell -NoProfile` for runbook blocks so your profile's aliases cannot shadow gh/git. Admin is needed only for scheduled tasks, services, and hosts-file edits — most gh/hf/git work does not need it.
