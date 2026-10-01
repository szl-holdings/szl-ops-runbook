# Runbook entries — part C: domains, Cloudflare, own-metal, org profile, local env, control plane.
ENTRIES = []

def add(**kw):
    ENTRIES.append(kw)

add(
    id="cf-tunnel-530",
    title="gpu / gateway / meter / meter2 .a-11-oy.com return 530 (error 1033) — cloudflared is down on the box",
    tags=["cloudflare", "tunnel", "own-metal", "530", "1033", "omen", "laptop"],
    surface="own-metal",
    severity="high",
    symptom="Public probes: `https://gpu.a-11-oy.com/` -> 530, `gateway`/`meter`/`meter2` -> 530, while `gpu2` -> 403 (Cloudflare Access, expected). DNS still resolves to Cloudflare anycast. Observed 2026-10-01 01:10Z: all four tunnel hosts 530. Cause: cloudflared not connected (process down after reboot/sleep, or tunnel-ID drift in the CNAMEs).",
    diagnose=r'''# From any machine: which hosts are down?
foreach ($h in "gateway","gpu","gpu2","meter","meter2","gdw","holdings") {
  try { $c = (Invoke-WebRequest -UseBasicParsing -Method Head "https://$h.a-11-oy.com/" -TimeoutSec 10).StatusCode } catch { $c = $_.Exception.Response.StatusCode.value__ }
  "{0,-8} {1}" -f $h, $c
}
# ON THE BOX (omen tower / betterwithage laptop), as Administrator:
cloudflared tunnel list
Get-Process cloudflared -ErrorAction SilentlyContinue | Select-Object Id, StartTime
Get-ScheduledTask -TaskName "*Tunnel*","*cloudflared*","*Ollama*","*Joule*","*LiteLLM*" -ErrorAction SilentlyContinue | Format-Table TaskName, State''',
    fix=r'''# Run the repo scripts you already ship (a11oy/box-scripts). Admin PowerShell 5.1 on EACH box:
$Root = (Resolve-Path -LiteralPath "$HOME\src\a11oy").Path; Set-Location -LiteralPath $Root
git pull --ff-only
powershell -ExecutionPolicy RemoteSigned -File .\box-scripts\SZL_MESH_RESTART.ps1    # starts persisted tasks, cloudflared, Ollama; probes hosts
# If MESH_RESTART reports 530 persisting on a host whose local service is up, the CNAME points at a stale tunnel ID:
powershell -ExecutionPolicy RemoteSigned -File .\box-scripts\SZL_TUNNEL_HEAL.ps1     # re-routes ingress hostnames to THIS tunnel (uses local cert.pem, no API token)
# Nothing persisted at all? Re-run the boot persist script for the box:
#   tower : powershell -ExecutionPolicy RemoteSigned -File .\box-scripts\omen_boot_persist.ps1
#   laptop: powershell -ExecutionPolicy RemoteSigned -File .\box-scripts\laptop_persist.ps1''',
    verify=r'''foreach ($h in "gateway","gpu","meter","meter2") { try { (Invoke-WebRequest -UseBasicParsing -Method Head "https://$h.a-11-oy.com/" -TimeoutSec 10).StatusCode } catch { "$h $($_.Exception.Response.StatusCode.value__)" } }
# 200 = up · 404 = tunnel up, nothing on the local port · 502/503 = tunnel up, local service down · 530 = tunnel not connected''',
    notes="This is the one failure class no agent can fix remotely: it needs shell on the box (or a physical restart). Local services behind the tunnel: Ollama 11434 (tailnet only), joule exporter 9471, LiteLLM 4000. The gdw witness and holdings pages are NOT tunnel-backed, which is why they stay 200 while gpu is 530.",
    sources=["https://github.com/szl-holdings/a11oy/blob/main/box-scripts/SZL_MESH_RESTART.ps1", "https://github.com/szl-holdings/a11oy/blob/main/box-scripts/SZL_TUNNEL_HEAL.ps1", "https://github.com/szl-holdings/a11oy/blob/main/box-scripts/SOVEREIGN_MESH_RUNBOOK.md"],
)

add(
    id="cf-apex-404-or-cert-mismatch",
    title="a-11-oy.com apex 404 / www certificate mismatch — custom-domain binding, keep the orange cloud",
    tags=["cloudflare", "dns", "custom-domain", "huggingface", "tls", "apex", "www"],
    surface="domains",
    severity="high",
    symptom="Apex serves an HF edge 404 or a TLS name mismatch while the backing Space `szlholdings-a11oy.hf.space` is healthy (incidents 2026-09-01 and 2026-09-30, a11oy#2389). Space health and custom-domain health are separate claims.",
    diagnose=r'''foreach ($u in "https://a-11-oy.com/","https://www.a-11-oy.com/","https://szlholdings-a11oy.hf.space/healthz","https://holdings.a-11-oy.com/") {
  try { $r = Invoke-WebRequest -UseBasicParsing -Method Head $u -TimeoutSec 15; "{0,-45} {1} server={2}" -f $u, $r.StatusCode, $r.Headers.Server } catch { "{0,-45} {1}" -f $u, $_.Exception.Message.Substring(0,[Math]::Min(60,$_.Exception.Message.Length)) }
}
Resolve-DnsName a-11-oy.com -Type A | Select-Object Name, IPAddress
Resolve-DnsName www.a-11-oy.com -Type CNAME -ErrorAction SilentlyContinue | Select-Object Name, NameHost
# HF side: provider stage for the custom domain (needs org token)
# (Invoke-RestMethod -Headers @{Authorization="Bearer <token>"} https://huggingface.co/api/spaces/SZLHOLDINGS/a11oy).runtime.domains''',
    fix=r'''# Rules that held through both incidents:
# 1. Apex and www stay PROXIED (orange cloud) in Cloudflare. Do NOT grey-cloud to make HF's domain row go READY.
# 2. www -> 301 to apex at the edge (Cloudflare redirect rule), or www CNAME (proxied) -> szlholdings-a11oy.hf.space.
# 3. Register the custom domain on the HF Space (org admin UI) and add the HF verification TXT (_huggingface.a-11-oy.com) WITHOUT dropping the proxy.
# 4. Never add a second HF custom domain for the same Space.
# Cloudflare via API (zone a-11-oy.com = 27911fb3d5ed874fdd4e844ed7f5e248):
$Tok = Read-Host -AsSecureString "Cloudflare API token (Zone:DNS:Edit, Zone:Read)"
$H = @{ Authorization = "Bearer " + [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Tok)) }
$Zone = "27911fb3d5ed874fdd4e844ed7f5e248"
(Invoke-RestMethod -Headers $H "https://api.cloudflare.com/client/v4/zones/$Zone/dns_records?per_page=100").result | Select-Object type, name, content, proxied | Format-Table -AutoSize
# patch a record to proxied (example):
# Invoke-RestMethod -Method Patch -Headers $H -ContentType application/json -Body '{"proxied":true}' "https://api.cloudflare.com/client/v4/zones/$Zone/dns_records/<record-id>"
Remove-Variable Tok, H''',
    verify=r'''(Invoke-WebRequest -UseBasicParsing https://a-11-oy.com/ -TimeoutSec 15).StatusCode; (Invoke-WebRequest -UseBasicParsing -MaximumRedirection 0 https://www.a-11-oy.com/ -TimeoutSec 15 -ErrorAction SilentlyContinue).StatusCode''',
    notes="a11oy.com (no dashes) is an unrelated third-party store — never link it. a11oy.net zone id is 6893093cd089c9994349bc16b0906006 (GitHub Pages: 4x A 185.199.108-111.153 + www CNAME szl-holdings.github.io). Public 200 on the proxied apex beats a green HF domain row; the Spaces health endpoint keeps the row DEGRADED until the provider says READY — that is honest, leave it.",
    sources=["https://github.com/szl-holdings/a11oy/blob/main/docs/SPACES_HEALTH_OPERATIONS.md", "https://github.com/szl-holdings/a11oy/issues/1497"],
)

add(
    id="cf-token-verify-and-dns-audit",
    title="Verify a Cloudflare token and dump both zones' DNS — before any write",
    tags=["cloudflare", "dns", "token", "audit", "a11oy.net", "a-11-oy.com"],
    surface="domains",
    severity="medium",
    symptom="A connector or script reports HTTP 400 code 6003 / 6103 (`Invalid format for X-Auth-Key header`) or 403; you need to know whether the token is live and what the zones hold right now.",
    diagnose=r'''$Tok = Read-Host -AsSecureString "Cloudflare API token"
$H = @{ Authorization = "Bearer " + [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Tok)) }
(Invoke-RestMethod -Headers $H https://api.cloudflare.com/client/v4/user/tokens/verify).result | Select-Object status, expires_on
$Zones = @{ "a-11-oy.com" = "27911fb3d5ed874fdd4e844ed7f5e248"; "a11oy.net" = "6893093cd089c9994349bc16b0906006" }
foreach ($z in $Zones.GetEnumerator()) {
  "== $($z.Key)"
  (Invoke-RestMethod -Headers $H "https://api.cloudflare.com/client/v4/zones/$($z.Value)/dns_records?per_page=200").result | Sort-Object type, name | Format-Table type, name, content, proxied, ttl -AutoSize
  (Invoke-RestMethod -Headers $H "https://api.cloudflare.com/client/v4/zones/$($z.Value)/dnssec").result | Select-Object status
}
Remove-Variable Tok, H''',
    fix=r'''# Token says anything but "active": regenerate in the Cloudflare dashboard with exactly Zone:DNS:Edit + Zone:Zone:Read on the two zones.
# Export a rollback bundle BEFORE writing anything:
# Invoke-RestMethod -Headers $H "https://api.cloudflare.com/client/v4/zones/<zone>/dns_records/export" | Set-Content -LiteralPath "$HOME\cf-<zone>-$(Get-Date -f yyyyMMdd).bind" -Encoding ASCII''',
    verify=r'''Resolve-DnsName a11oy.net -Type NS | Select-Object NameHost; Resolve-DnsName a-11-oy.com -Type NS | Select-Object NameHost''',
    notes="Both zones validated DNSSEC (DS at parent) as of 2026-10-01. One writer at a time: concurrent DNS edits from two sessions produced conflicting observations on 2026-08-31 — finish one change, read it back, then start the next.",
    sources=["https://github.com/szl-holdings/szl-v14/blob/main/OPERATOR_PACKET.md"],
)

add(
    id="gh-pages-custom-domain",
    title="GitHub Pages site (a11oy.net, dev.a-11-oy.com) not serving or wrong cert — CNAME file + DNS + Pages config",
    tags=["github-pages", "dns", "a11oy.net", "dev", "custom-domain"],
    surface="domains",
    severity="medium",
    symptom="a11oy.net (repo `a11oy-net`) or dev.a-11-oy.com (repo `szl-platform`, branch gh-pages) returns 404, a GitHub 'There isn't a GitHub Pages site here', or a certificate for the wrong name.",
    diagnose=r'''gh api repos/szl-holdings/a11oy-net/pages --jq '{cname,status,https_enforced,source}'
gh api repos/szl-holdings/szl-platform/pages --jq '{cname,status,https_enforced,source}'
Resolve-DnsName dev.a-11-oy.com -Type CNAME | Select-Object NameHost
Resolve-DnsName a11oy.net -Type A | Select-Object IPAddress''',
    fix=r'''# Pages needs all three to agree: (1) DNS -> szl-holdings.github.io (CNAME, DNS-only for subdomains) or the 4 GitHub A records for an apex,
# (2) a CNAME file at the published root containing exactly the hostname, (3) the repo Pages setting with that custom domain.
gh api -X PUT repos/szl-holdings/a11oy-net/pages -f cname=a11oy.net -F https_enforced=true
# Re-request the certificate after a DNS fix:
gh api -X POST repos/szl-holdings/a11oy-net/pages/builds''',
    verify=r'''(Invoke-WebRequest -UseBasicParsing https://a11oy.net/health.json).StatusCode; (Invoke-WebRequest -UseBasicParsing https://dev.a-11-oy.com/).Headers.Server''',
    notes="Only one custom domain per Pages site; a second one on the same org site fails (that is why dev.a-11-oy.com moved to the szl-platform gh-pages branch). The org SHA-pin rule forbids the official Pages actions, so the pages-sync workflow pushes the built tree to gh-pages itself.",
    sources=["https://github.com/szl-holdings/szl-platform/blob/main/docs/OPERATOR_PACKET.md"],
)

add(
    id="own-metal-services",
    title="Ollama / joule exporter / LiteLLM down behind a live tunnel (502/503/404) — restart the local stack",
    tags=["own-metal", "ollama", "litellm", "energy", "exporter", "scheduled-task"],
    surface="own-metal",
    severity="medium",
    symptom="Tunnel host answers 502/503 (tunnel connected, local service down) or 404 (nothing on the port). `/api/a11oy/v1/code/health` on the product no longer says `self-hosted-gpu`.",
    diagnose=r'''Get-Process ollama, cloudflared, python, litellm -ErrorAction SilentlyContinue | Select-Object ProcessName, Id, StartTime
Test-NetConnection 127.0.0.1 -Port 11434 -InformationLevel Quiet   # Ollama
Test-NetConnection 127.0.0.1 -Port 9471  -InformationLevel Quiet   # joule exporter
Test-NetConnection 127.0.0.1 -Port 4000  -InformationLevel Quiet   # LiteLLM
nvidia-smi --query-gpu=name,power.draw,memory.used --format=csv''',
    fix=r'''# Preferred: the persisted scheduled tasks
Get-ScheduledTask -TaskName "*Ollama*","*Joule*","*LiteLLM*","*Tunnel*" -ErrorAction SilentlyContinue | Where-Object State -ne Running | Start-ScheduledTask
# Direct, if a task is missing:
Start-Process -WindowStyle Hidden -FilePath (Get-Command ollama).Source -ArgumentList "serve"
$Root = (Resolve-Path -LiteralPath "$HOME\src\a11oy").Path; Set-Location -LiteralPath $Root
Start-Process -WindowStyle Hidden python -ArgumentList "box-scripts\omen_joule_exporter.py"
Start-Process -WindowStyle Hidden litellm -ArgumentList "--config box-scripts\litellm_config.yaml --port 4000"''',
    verify=r'''Invoke-RestMethod http://127.0.0.1:11434/api/tags | Select-Object -ExpandProperty models | Select-Object name
(Invoke-RestMethod https://a-11-oy.com/api/a11oy/v1/code/health).inference''',
    notes="Ollama stays tailnet-only — never expose 11434 through the tunnel. Energy claims: per-request joules are MEASURED only while the exporter and NVML are live; when they are not, the product must show UNAVAILABLE, and it does. Do not fake a healthy mesh in a demo.",
    sources=["https://github.com/szl-holdings/a11oy/blob/main/box-scripts/SZL_MESH_RESTART.ps1", "https://github.com/szl-holdings/platform/blob/main/replit-sync/FOUNDER_GPU_RUNBOOK.md"],
)

add(
    id="estate-probe",
    title="Probe every public surface in one pass — the expected codes",
    tags=["probe", "status", "domains", "huggingface", "monitoring"],
    surface="domains",
    severity="low",
    symptom="You want the truth table for the estate before a demo, after a deploy, or when something feels off.",
    diagnose=r'''$Targets = [ordered]@{
  "https://a-11-oy.com/"                              = 200
  "https://www.a-11-oy.com/"                          = 200
  "https://a-11-oy.com/verify"                        = 200
  "https://a-11-oy.com/code"                          = 200
  "https://a-11-oy.com/killinchu"                     = 200
  "https://a-11-oy.com/api/a11oy/v1/honest"           = 200
  "https://a-11-oy.com/healthz"                       = 200
  "https://a11oy.net/"                                = 200
  "https://a11oy.net/spec/GovernedAction/v1"          = 200
  "https://a11oy.net/health.json"                     = 200
  "https://holdings.a-11-oy.com/"                     = 200
  "https://dev.a-11-oy.com/"                          = 200
  "https://gdw.a-11-oy.com/healthz"                   = 200
  "https://szlholdings-a11oy.hf.space/healthz"        = 200
  "https://szlholdings-killinchu.hf.space/"           = 200
  "https://szlholdings-llm-router-live.hf.space/"     = 200
  "https://szlholdings-prove-it.static.hf.space/"     = 200
  "https://szlholdings-gdw-frontier.hf.space/"        = 401   # auth-guarded witness, 401 is correct
  "https://gpu2.a-11-oy.com/"                         = 403   # Cloudflare Access, 403 is correct
  "https://gpu.a-11-oy.com/"                          = 200   # 530 => see cf-tunnel-530
  "https://gateway.a-11-oy.com/"                      = 200
  "https://meter.a-11-oy.com/"                        = 200
}
foreach ($t in $Targets.GetEnumerator()) {
  try { $c = (Invoke-WebRequest -UseBasicParsing -Method Head $t.Key -TimeoutSec 15 -MaximumRedirection 2).StatusCode } catch { $c = $_.Exception.Response.StatusCode.value__; if (-not $c) { $c = "ERR" } }
  $mark = if ("$c" -eq "$($t.Value)") { "ok  " } else { "DIFF" }
  "{0} {1,-5} expected {2,-4} {3}" -f $mark, $c, $t.Value, $t.Key
}''',
    fix=r'''# Any DIFF maps to an entry: 530 -> cf-tunnel-530 · apex 404/TLS -> cf-apex-404-or-cert-mismatch · Space 5xx -> hf-space-paused-or-sleeping / hf-space-stale-image · Pages 404 -> gh-pages-custom-domain''',
    verify=r'''# All rows 'ok' is the demo-ready state. Save the output with the date next to the receipt you are about to show.''',
    notes="Snapshot 2026-10-01 01:10Z: every row ok except gpu/gateway/meter/meter2 = 530 (own-metal tunnel down). szlholdings.com has no working TLS and www.szlholdings.com does not resolve — known owner-level item, not part of the product estate.",
    sources=[],
)

add(
    id="org-profile-validators",
    title="szl-holdings org profile red on Tests / SZL Router flagship alignment / estate alignment — required blocks and word budgets",
    tags=[".github", "profile", "front-door", "validators", "org", "huggingface-card"],
    surface="github",
    severity="high",
    symptom="After editing `profile/README.md` (or `huggingface/org-card/README.md`), `.github` main goes red: `Tests` -> `truth boundary marker must remain on every front door: SIMULATED/HISTORICAL`; `SZL Router flagship alignment` -> `GitHub profile missing SZL Router ...`; `Exact taxonomy, front doors, and publication set` -> `GitHub profile missing Killinchu/Terra/PRISM Counsel/...`. This happened on 2026-10-01 after the 'AI that signs its work' rewrite.",
    diagnose=r'''$Root = (Resolve-Path -LiteralPath "$HOME\src\.github").Path; Set-Location -LiteralPath $Root
git fetch origin; git checkout main; git pull --ff-only
(Get-Content profile\README.md -Raw).Split(" `n", [StringSplitOptions]::RemoveEmptyEntries).Count   # must be <= 430 words
(Get-Content huggingface\org-card\README.md -Raw).Split(" `n", [StringSplitOptions]::RemoveEmptyEntries).Count   # <= 380 words
python .github\scripts\public_front_door_check.py | Select-String '"state"|failures' -Context 0,6
python .github\scripts\router_flagship_contract.py | Select-String '"status"|missing'
python .github\scripts\estate_alignment_contract.py --output $env:TEMP\ea.json; (Get-Content $env:TEMP\ea.json | ConvertFrom-Json).failures''',
    fix=r'''# The profile MUST contain all of these (case-insensitive where the script folds):
#  Router block : "SZL Router", "szl-holdings/szl-router", "SZLHOLDINGS/llm-router-live", "https://a-11-oy.com/code", "https://a11oy.net",
#                 "one inference flagship", "three commercial flagships", "five public domain bodies", "six internal engines",
#                 "not availability, operational readiness, or publication policy"
#  Truth markers: "Current state", "HISTORICAL", "SIMULATED"   (exact case; also required in the Hub card and the static front door HTML)
#  Historical contract: "16 portfolio Spaces", "1 inventory-only Space", "45 models", "34 datasets", and the names
#                 A11oy, Forge, Killinchu, Terra, PRISM Counsel, PURIQ Finance, LYTE
#  Canonical image: ./assets/evidence-lattice-v2.webp ; banned copy: "every model ships with signed receipts", "70+ live surfaces", "trust ceiling 0.97", "all models operational"
# A verified-passing profile (420 words, all three validators green locally on 2026-10-01) is kept at:
#   szl-ops-runbook/templates/org-profile-README.md
Copy-Item ..\szl-ops-runbook\templates\org-profile-README.md profile\README.md -Force
git checkout -b fix/profile-restore-required-blocks
git add profile\README.md; git commit -s -m "fix(profile): restore inference-flagship block, HISTORICAL contract, and truth-boundary markers"
git push -u origin fix/profile-restore-required-blocks
gh pr create --repo szl-holdings/.github --fill --body-file ..\szl-ops-runbook\templates\pr-body.md''',
    verify=r'''python .github\scripts\public_front_door_check.py | Select-String '"state"'
python .github\scripts\router_flagship_contract.py | Select-String '"status"'
python .github\scripts\estate_alignment_contract.py --output $env:TEMP\ea.json; (Get-Content $env:TEMP\ea.json | ConvertFrom-Json).state''',
    notes="Run the three scripts locally BEFORE pushing any profile or Hub-card copy change; they are fast and network-free. The Hub card has the same markers plus a 380-word budget, the 🛡️ emoji, a 60-char short description, and the router SVG URL. PR #816 restored only the markers and still failed the router and taxonomy gates — restore all three blocks together.",
    sources=["https://github.com/szl-holdings/.github/blob/main/.github/scripts/public_front_door_check.py", "https://github.com/szl-holdings/.github/blob/main/.github/scripts/router_flagship_contract.py", "https://github.com/szl-holdings/.github/actions/runs/36798458762"],
)

add(
    id="ps51-gotchas",
    title="Windows PowerShell 5.1 gotchas that have eaten whole sessions",
    tags=["powershell", "windows", "local", "paste", "encoding"],
    surface="local",
    severity="medium",
    symptom="A pasted block hangs at `>>`, aborts on the first native stderr line, mangles em-dashes/arrows, refuses to run a downloaded .ps1, or a 25 KB paste silently truncates.",
    diagnose=r'''$PSVersionTable.PSVersion
Get-ExecutionPolicy -List
[Console]::OutputEncoding.WebName; $OutputEncoding.WebName''',
    fix=r'''# 1. '>>' prompt = unfinished construct. Ctrl+C until you see 'PS ...>' again, then paste ONE complete unit (no copied prompt markers).
# 2. Native stderr under Stop aborts the script (gh/git/python write progress to stderr). Wrap native calls:
function Invoke-Native { param([string]$Exe, [string[]]$Args) $o = & $Exe @Args 2>&1; if ($LASTEXITCODE -ne 0) { throw "$Exe exited $LASTEXITCODE`n$($o -join "`n")" }; $o }
#    or run with  $ErrorActionPreference = "Continue"  around gh/git and test $LASTEXITCODE yourself.
# 3. Save scripts ASCII-only or UTF-8 WITH BOM; 5.1 misreads BOM-less UTF-8 (box-scripts are ASCII on purpose).
Set-Content -LiteralPath .\x.ps1 -Value $Text -Encoding UTF8   # 5.1's UTF8 writes a BOM
# 4. Downloaded file: unblock, then run with a clean host
Unblock-File .\szl-handle-all.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\szl-handle-all.ps1
# 5. Long payloads: ship a .ps1 file + 2-line launcher instead of a 300-line paste (the Chaski gate JSON hand-paste broke this way).
# 6. Relative paths resolve against the child process cwd — always Resolve-Path and pass absolute paths to python/gh.''',
    verify=r'''# A clean unit ends at a normal prompt with the final line printed by your script, not by the host.''',
    notes="Prefer `powershell -NoProfile` for runbook blocks so your profile's aliases cannot shadow gh/git. Admin is needed only for scheduled tasks, services, and hosts-file edits — most gh/hf/git work does not need it.",
    sources=[],
)

add(
    id="pnpm-web-build-fails-locally",
    title="a11oy / platform web monorepo won't build in a fresh sandbox — unwired pnpm workspace deps",
    tags=["pnpm", "node", "build", "a11oy", "platform", "monorepo"],
    surface="local",
    severity="medium",
    symptom="`pnpm install` or `pnpm -r build` fails with unresolved workspace packages, Node version mismatch (Node 24 expected), or Vite/typecheck errors that CI does not show.",
    diagnose=r'''node -v; pnpm -v
$Root = (Resolve-Path -LiteralPath "$HOME\src\a11oy").Path; Set-Location -LiteralPath $Root
Get-Content pnpm-workspace.yaml; Get-Content package.json | ConvertFrom-Json | Select-Object -ExpandProperty engines''',
    fix=r'''# Match CI exactly
corepack enable; corepack prepare pnpm@latest --activate
nvm use 24   # or fnm use 24
pnpm install --frozen-lockfile
pnpm -r --filter "./web/..." build
# a11oy's operational Hub surface is produced by the payload target, not by a dev server:
pnpm payload:huggingface
# doctrine demo:
pnpm test:doctrine''',
    verify=r'''Get-ChildItem web\dist -Recurse -Filter index.html | Select-Object FullName''',
    notes="a11oy is a TypeScript library workspace with a Python serving layer, not a Docker-first web app; treat `pnpm payload:huggingface` as the artifact. CI has a bundle-integrity guard (a11oy#718) for stale chunk 404s — if a Space shows a chunk 404, rebuild and republish rather than shimming.",
    sources=["https://github.com/szl-holdings/a11oy/pull/718", "https://github.com/szl-holdings/platform/pull/398"],
)

add(
    id="model-gates-not-promotable",
    title="szl-typesafe-triage: receipt verification red, 11 of 12 gates — publish evidence, do not promote",
    tags=["models", "qualification", "gates", "szl-forge", "typesafe-triage", "huggingface"],
    surface="models",
    severity="medium",
    symptom="A five-seed study passes 11 of 12 release gates; `receipt verification` stays red; a text-only repair and passing local tests exist but no fresh evaluation and no new verified release receipt.",
    diagnose=r'''$Root = (Resolve-Path -LiteralPath "$HOME\src\szl-typesafe-triage").Path; Set-Location -LiteralPath $Root
git pull --ff-only
Get-ChildItem out\train\study -Recurse -Filter "*gate*" | Select-Object FullName | Select-Object -First 10
python -m pytest -q tests 2>&1 | Select-Object -Last 3''',
    fix=r'''# The order is fixed: pinned inputs -> isolated challenger -> frozen evaluation -> receipts -> publication gate -> promotion gate.
# 1. Re-run the frozen evaluation on the repaired candidate with byte-identical holdouts (never re-grade the published numbers in prose).
# 2. Emit a NEW release receipt and verify it offline:
python scripts\verify_release_receipt.py out\train\study\release-receipt.json
# 3. Only when 12/12 are green: publish the card (evidence-published), THEN open the separate promotion review.''',
    verify=r'''python scripts\verify_release_receipt.py out\train\study\release-receipt.json; $LASTEXITCODE''',
    notes="Publication is not promotion. A model may be evidence-published at 11/12 with the red gate stated on the card; it may not be routed as production until receipt verification is green. The eval script that produced the historical 12-case DEV result is not hash-bound by the receipt — a new grader written from scratch would manufacture evidence, so search your laptop for the original before rewriting.",
    sources=["https://github.com/szl-holdings/szl-typesafe-triage", "https://huggingface.co/SZLHOLDINGS/szl-triage-qwen3.5-0.8b-lora-study5"],
)

add(
    id="deadman-census-red",
    title="'Estate dead-man supervisor' / 'Estate readiness evidence' red — census fails closed on completeness",
    tags=[".github", "szl-estate-os", "szl-org-health", "scheduler", "census", "credentials"],
    surface="github",
    severity="medium",
    symptom="Scheduled lanes fail every cycle: `.github` Estate dead-man supervisor, `szl-estate-os` Estate readiness evidence, `szl-frontier` Estate outside-seat verifier. Logs show tests green and then a final `exit 1` from the completeness gate (GitHub collection covered only a fallback subset, or no authenticated HF inventory reached the job).",
    diagnose=r'''$Run = gh run list --repo szl-holdings/.github --workflow "Estate dead-man supervisor" --limit 1 --json databaseId --jq '.[0].databaseId'
gh run view $Run --repo szl-holdings/.github --log 2>$null | Select-String "UNKNOWN|fallback|subset|credential|HF_|token|incomplete" | Select-Object -Last 15
gh secret list --repo szl-holdings/.github --json name --jq '[.[].name]' ''',
    fix=r'''# Repair is credential-alias + scope alignment, never weakening the gate:
# - the job must receive the governed GitHub identity (SZL_GITHUB_TOKEN or the qillqaq App) with org read scope, and
# - an HF read token under the name the collector reads (check the workflow env block for the exact name).
gh secret set <NAME> --repo szl-holdings/.github   # value from secure prompt
gh workflow run "Estate dead-man supervisor" --repo szl-holdings/.github''',
    verify=r'''gh run list --repo szl-holdings/.github --workflow "Estate dead-man supervisor" --limit 1 --json conclusion''',
    notes="A healthy public-estate SRE run cannot clear a failed census; they are separately witnessed on purpose. szl-estate-os runs are not readable through `gh run view --log` when the job list is 404 (private + retention) — open the run URL instead.",
    sources=["https://github.com/szl-holdings/szl-org-health/issues/39", "https://github.com/szl-holdings/.github/issues/684"],
)

add(
    id="secret-health-unavailable",
    title="secret-health reports UNAVAILABLE — qillqaq App permission, not a new PAT",
    tags=[".github", "secrets", "qillqaq", "github-app", "policy"],
    surface="github",
    severity="low",
    symptom="`.github/workflows/secret-health.yml` reports required secret names as UNAVAILABLE across repos.",
    diagnose=r'''gh run list --repo szl-holdings/.github --workflow "secret-health" --limit 1 --json conclusion,url | ConvertFrom-Json
gh api orgs/szl-holdings/installations --jq '.installations[]|{app_slug,permissions}' 2>$null''',
    fix=r'''# Approve the qillqaq GitHub App's read-only Secrets permission upgrade in the org settings (owner action). No source change needed afterwards.
# Until then the lane falls back to SZL_GITHUB_TOKEN; keep that token governed. Do NOT mint another long-lived PAT for this audit.''',
    verify=r'''gh workflow run secret-health.yml --repo szl-holdings/.github; Start-Sleep 120; gh run list --repo szl-holdings/.github --workflow "secret-health" --limit 1 --json conclusion''',
    notes="UNAVAILABLE means 'could not read authoritatively'; it is never relabeled MISSING. Name presence does not prove a token is valid (see hf-deploy-400-401-token).",
    sources=["https://github.com/szl-holdings/szl-doctrine/blob/main/FOUNDER_SECRETS_RUNBOOK.md"],
)

add(
    id="secret-scanning-false-positive-vendored",
    title="Secret-scanning alert points into vendored site-packages (committed venv) — verify, then resolve as false positive",
    tags=["security", "secret-scanning", "szl-forge", "venv", "false-positive"],
    surface="github",
    severity="medium",
    symptom="Secret scanning reports e.g. a 'Mistral AI API Key' in `.venv-chaski-r3-gpu/Lib/site-packages/transformers/...` (szl-forge alert #2, 2026-09-18). The 'secret' is a pattern match inside library source from a virtualenv that was committed once; validity shows `inactive`; the path is absent from HEAD.",
    diagnose=r'''$Repo = "szl-holdings/szl-forge"; $N = 2
gh api "repos/$Repo/secret-scanning/alerts/$N" --jq '{state,validity,publicly_leaked,push_protection_bypassed,secret_type_display_name,html_url}'
gh api "repos/$Repo/secret-scanning/alerts/$N/locations" --jq '.[]|{type,path:.details.path,line:.details.start_line,commit:.details.commit_sha[0:10]}'
# Is the path still in HEAD? (404 = gone)
gh api "repos/$Repo/contents/.venv-chaski-r3-gpu" --jq 'if type=="array" then "PRESENT" else .message end' ''',
    fix=r'''# Only after the three facts above agree (validity inactive, path is library source, path absent from HEAD):
gh api -X PATCH "repos/$Repo/secret-scanning/alerts/$N" -f state=resolved -f resolution=false_positive -f resolution_comment="Pattern match inside vendored transformers source in a since-removed committed venv (commit 7dfba5d8); validity inactive; path absent from HEAD."
# If validity were 'active' or the match were in YOUR code: rotate the key at the provider FIRST, then resolve as 'revoked'.
# Keep venvs out of the tree for good (.gitignore already has .venv-ra-v2/, .venv-ra-v3/, khipu/.venv/):
Add-Content -LiteralPath .gitignore -Value ".venv*/" ''',
    verify=r'''gh api "repos/$Repo/secret-scanning/alerts?state=open" --jq 'length' ''',
    notes="This closure is a security decision; the audit agent prepares the evidence and the owner clicks. Org-wide at 2026-10-01 02:15Z: 1 open secret-scanning alert (this one), 1 open Dependabot alert (platform, npm, low). Push protection and secret scanning are enforced on every repo by managed configuration 252588.",
    sources=["https://github.com/szl-holdings/szl-forge/security/secret-scanning/2"],
)

add(
    id="codeql-scorecard-backlog",
    title="Code-scanning backlog: 467 open alerts across 18 repos, 240 are PinnedDependenciesID — the wave plan",
    tags=["security", "codeql", "scorecard", "pinned-dependencies", "token-permissions", "ssrf", "dangerous-workflow"],
    surface="github",
    severity="high",
    symptom="Per-repo code-scanning counts at 2026-10-01: a11oy 100+ (list truncated), szl-forge 83, david-leads 76, killinchu 50, .github 50, vertical-services 38, immune 27, anatomy 22, szl-router 20. By rule: PinnedDependenciesID 240, TokenPermissionsID 40, py/empty-except 29, py/stack-trace-exposure 12, py/incomplete-url-substring-sanitization 8. Critical (7): DangerousWorkflowID in .github estate-one-fabric-alignment.yml (2), david-leads frontier-live-canary.yml (1), szl-router hf-space-drift-check.yml (1); py/partial-ssrf in david-leads app/signals.py:34, vertical-services services/finance/feed.py:35 and deploy/szl_verticals/connector_transport.py:27.",
    diagnose=r'''foreach ($r in "a11oy","szl-forge","david-leads","killinchu",".github","vertical-services","immune","szl-router") {
  $items = gh api --paginate --slurp "repos/szl-holdings/$r/code-scanning/alerts?state=open&per_page=100" 2>$null | ConvertFrom-Json | ForEach-Object { $_ }
  $byRule = $items | Group-Object { $_.rule.id } | Sort-Object Count -Descending | Select-Object -First 5 | ForEach-Object { "$($_.Name)=$($_.Count)" }
  "{0,-18} open={1,-4} {2}" -f $r, @($items).Count, ($byRule -join " ")
}''',
    fix=r'''# Wave order (highest risk first, each its own PR per repo, body with the seven provenance headings):
# 1. DangerousWorkflowID (critical): never run checked-out PR/workflow_run head code in a privileged context.
#    Pattern: checkout the TRUSTED base for scripts, pass untrusted head SHA only as data; or split into an unprivileged
#    pull_request job + a workflow_run job that only reads artifacts. Then dismiss remaining as 'used in tests' only with evidence.
# 2. py/partial-ssrf (critical): build outbound URLs from an allowlisted host table, never from request input; reject
#    anything not in the allowlist before the HTTP call (david-leads signals.py:34, vertical-services feed.py:35, connector_transport.py:27).
# 3. py/stack-trace-exposure (12): return a generic error body; log the traceback server-side with a correlation id.
# 4. TokenPermissionsID (40): top-level `permissions: {}` or `contents: read` in every workflow; grant per job.
# 5. PinnedDependenciesID (240): pin Docker base images by digest, pip installs with --require-hashes (pip-compile --generate-hashes),
#    GitHub Actions by 40-hex SHA (org rule already). Do it repo by repo; szl-forge (75) and .github (31) first.
# 6. Hygiene (py/empty-except 29, unused imports): ruff --fix in a dedicated PR per repo.''',
    verify=r'''gh api "repos/szl-holdings/<repo>/code-scanning/alerts?state=open&per_page=1" --jq 'length' ''',
    notes="Scorecard findings (PinnedDependenciesID, TokenPermissionsID, FuzzingID, CIIBestPracticesID, CodeReviewID, MaintainedID) are posture probes, not exploitable bugs; the CodeQL py/* and DangerousWorkflowID findings are the ones that can hurt. Do not bulk-dismiss to make a number go green. Org-level code-scanning listing needs a security-manager token (401 at 2026-10-01); per-repo listing works.",
    sources=["https://github.com/szl-holdings/.github/security/code-scanning/263", "https://github.com/szl-holdings/david-leads/security/code-scanning/7", "https://github.com/szl-holdings/vertical-services/security/code-scanning/20"],
)

add(
    id="org-rulesets-admin-org",
    title="Protect every default branch at once — org ruleset (needs admin:org; connector token cannot)",
    tags=["github", "org", "rulesets", "branch-protection", "admin", "enterprise"],
    surface="github",
    severity="high",
    symptom="szl-org-health#176 found 52 of 97 active repositories without protected default branches; `.github#649` asks for exact-head gates on core mains. The connected automation token lacks `admin:org`, so `GET /orgs/szl-holdings/rulesets` returns 404 and org rulesets cannot be created by agents.",
    diagnose=r'''gh auth status 2>&1 | Select-String "Token scopes"
gh api orgs/szl-holdings/rulesets 2>&1 | Select-Object -First 3''',
    fix=r'''# Owner console (your own login, admin:org). Ruleset 1 is zero-risk: no deletes, no force-pushes on any default branch.
gh auth refresh -h github.com -s admin:org,repo,workflow
$Rules = @'
{ "name": "szl-default-branch-integrity", "target": "branch", "enforcement": "active",
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] },
                  "repository_name": { "include": ["~ALL"], "exclude": [], "protected": false } },
  "rules": [ { "type": "deletion" }, { "type": "non_fast_forward" } ],
  "bypass_actors": [ { "actor_id": 1, "actor_type": "OrganizationAdmin", "bypass_mode": "always" } ] }
'@
$Rules | gh api -X POST orgs/szl-holdings/rulesets --input -
# Ruleset 2 (flagships only): PRs required before merge on main; apps keep their lanes via bypass if needed.
$Flag = @'
{ "name": "szl-flagship-pr-required", "target": "branch", "enforcement": "active",
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] },
                  "repository_name": { "include": ["a11oy","killinchu","platform",".github","szl-router","david-leads","szl-substrate","szl-forge"], "exclude": [], "protected": false } },
  "rules": [ { "type": "pull_request", "parameters": { "required_approving_review_count": 0, "dismiss_stale_reviews_on_push": false, "require_code_owner_review": false, "require_last_push_approval": false, "required_review_thread_resolution": false } } ],
  "bypass_actors": [ { "actor_id": 1, "actor_type": "OrganizationAdmin", "bypass_mode": "pull_request" } ] }
'@
$Flag | gh api -X POST orgs/szl-holdings/rulesets --input -''',
    verify=r'''gh api orgs/szl-holdings/rulesets --jq '.[]|"\(.id) \(.name) \(.enforcement)"'
gh api repos/szl-holdings/szl-pin/rules/branches/main --jq '.[].type' ''',
    notes="Org rulesets apply to repos the moment they are created (`~ALL`), which is how 52 repos get protected in one call and stay protected. Do not set required status checks org-wide: repos without those checks would never merge again. Enterprise plan, 3 seats, 2FA required, members cannot create public repos — confirmed 2026-10-01.",
    sources=["https://github.com/szl-holdings/szl-org-health/issues/176", "https://github.com/szl-holdings/.github/issues/649"],
)

add(
    id="showcase-custom-domain",
    title="showcase.a-11-oy.com — GitHub Pages for szl-showcase needs one Cloudflare CNAME (connector token broken)",
    tags=["showcase", "github-pages", "cloudflare", "dns", "a-11-oy.com"],
    surface="domains",
    severity="medium",
    symptom="Repo szl-holdings/szl-showcase is public with Pages enabled (source main:/), CNAME file and Pages custom domain set to showcase.a-11-oy.com, but DNS has no record yet; the Cloudflare connector fails auth (code 9106), so the record must be created from the owner console. Until then the page is live at https://szl-showcase.pplx.app.",
    diagnose=r'''gh api repos/szl-holdings/szl-showcase/pages --jq '{status,cname,https_enforced,protected_domain_state}'
Resolve-DnsName showcase.a-11-oy.com -Type CNAME -ErrorAction SilentlyContinue | Select-Object NameHost''',
    fix=r'''$Tok = Read-Host -AsSecureString "Cloudflare API token (Zone:DNS:Edit on a-11-oy.com)"
$H = @{ Authorization = "Bearer " + [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Tok)); "Content-Type" = "application/json" }
$Zone = "27911fb3d5ed874fdd4e844ed7f5e248"
$Body = '{"type":"CNAME","name":"showcase","content":"szl-holdings.github.io","ttl":1,"proxied":false}'
Invoke-RestMethod -Method Post -Headers $H -Body $Body "https://api.cloudflare.com/client/v4/zones/$Zone/dns_records" | Select-Object -ExpandProperty result | Select-Object name, content, proxied
Remove-Variable Tok, H
# After GitHub provisions the certificate (minutes to an hour):
gh api -X PUT repos/szl-holdings/szl-showcase/pages -F https_enforced=true''',
    verify=r'''(Invoke-WebRequest -UseBasicParsing https://showcase.a-11-oy.com/ -TimeoutSec 20).StatusCode''',
    notes="DNS-only (grey cloud) is required while GitHub issues the certificate; it can be proxied afterwards if you want Cloudflare headers, but holdings.a-11-oy.com already works grey. Decide later whether holdings.a-11-oy.com (the older landing) redirects to showcase or the reverse — two landings is a duplicate surface under doctrine.",
    sources=["https://github.com/szl-holdings/szl-showcase"],
)
