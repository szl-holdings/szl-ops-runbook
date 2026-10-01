# Runbook entries — part B: Hugging Face estate.
ENTRIES = []

def add(**kw):
    ENTRIES.append(kw)

add(
    id="hf-deploy-400-401-token",
    title="HF Space/dataset deploy fails 400 Bad Request or 401 — HF_TOKEN missing or rotated",
    tags=["huggingface", "github-actions", "secrets", "deploy", "token"],
    surface="huggingface",
    severity="high",
    symptom="Reusable HF deployer prints `HF_TOKEN is not configured for the reusable deployer`, then `huggingface_hub.errors.BadRequestError ... 400` on `/api/spaces/SZLHOLDINGS/<space>/tree/main` (yarqa 2026-09-30, szl-gpu-bridge 2026-09-29). david-leads echoes `HTTP Error 401` from its dataset reader. Root cause on 2026-09-30: HF tokens were revoked and rotated; repository/org secrets still hold the old value or none.",
    diagnose=r'''# Which repos declare the secret (names only, never values)
foreach ($r in "yarqa","szl-gpu-bridge","david-leads","puriq-live","sda","szl-sovereign-os","governance-as-code") {
  $names = gh secret list --repo "szl-holdings/$r" --json name --jq '[.[].name]' 2>$null
  "{0,-20} {1}" -f $r, $names
}
gh secret list --org szl-holdings --json name,visibility --jq '.[]|"\(.name) \(.visibility)"' 2>$null
# Is the token you hold valid and scoped to the org?
hf auth whoami 2>&1 | Select-Object -First 6''',
    fix=r'''# 1. Mint ONE fine-grained HF token (write to the SZLHOLDINGS org repos that CI publishes). Store it once, org-wide:
#    (paste happens in the secure prompt; the value never lands in history)
$Tok = Read-Host -AsSecureString "Paste new HF write token"
$Plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Tok))
$Plain | gh secret set HF_TOKEN --org szl-holdings --visibility all
# Repos that use a differently named secret keep working only if you set that name too:
$Plain | gh secret set HF_ORG_TOKEN --org szl-holdings --visibility all
# david-leads reader (read-only, dataset-scoped token) is an ENVIRONMENT secret:
$Rd = Read-Host -AsSecureString "Paste DAVID_DATASET_READ_TOKEN (read-only)"
[Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Rd)) | gh secret set DAVID_DATASET_READ_TOKEN --repo szl-holdings/david-leads --env david-space-ci
Remove-Variable Plain, Tok, Rd
# 2. Re-run the failed lanes
gh run rerun (gh run list --repo szl-holdings/yarqa --workflow "HF Space deploy" --limit 1 --json databaseId --jq '.[0].databaseId') --repo szl-holdings/yarqa --failed
gh run rerun (gh run list --repo szl-holdings/szl-gpu-bridge --workflow "Sync training-receipts card" --limit 1 --json databaseId --jq '.[0].databaseId') --repo szl-holdings/szl-gpu-bridge --failed''',
    verify=r'''gh run list --repo szl-holdings/yarqa --workflow "HF Space deploy" --limit 1 --json conclusion,url | ConvertFrom-Json
Invoke-WebRequest -UseBasicParsing -Method Head https://szlholdings-yarqa.hf.space/ | Select-Object StatusCode''',
    notes="A 400 from `/tree/main?recursive=true` with huggingface_hub almost always means the request went out with an empty or invalid Authorization header, not a malformed path. PRECEDENCE TRAP (confirmed 2026-10-01): repository-level secrets shadow organization-level secrets of the same name. 43 repos carried repo-level HF_TOKEN / HF_ORG_TOKEN / HF_ORG_TOKEN1 / HF_WRITE_TOKEN / HUGGINGFACE_TOKEN / HUGGING_FACE_HUB_TOKEN set before the rotation, so setting the org secret alone changed nothing for them; remove the repo-level copies (OWNER-ONLY.ps1 part 2) or re-set each. Secret health reports PRESENT/MISSING/UNAVAILABLE by name; it cannot tell you a present token is dead — only a whoami or a rerun can.",
    sources=["https://github.com/szl-holdings/yarqa/actions/runs/36777783270", "https://github.com/szl-holdings/szl-gpu-bridge/actions/runs/36619758238", "https://github.com/szl-holdings/david-leads/actions/runs/36619707908", "https://github.com/szl-holdings/szl-doctrine/blob/main/FOUNDER_SECRETS_RUNBOOK.md"],
)

add(
    id="hf-space-stale-image",
    title="Space reports RUNNING on the new commit but serves old code (routes 404) — factory rebuild",
    tags=["huggingface", "space", "docker", "rebuild", "killinchu", "a11oy"],
    surface="huggingface",
    severity="high",
    symptom="GitHub `main` has the route; the live Space returns 404 for it; `/api/<app>/openapi.json` path count is lower than a local repro. Seen on killinchu 2026-06-05 (live 231 vs repro 250 paths) and again on 2026-07-06. Space UI says RUNNING at the new SHA.",
    diagnose=r'''$Space = "SZLHOLDINGS/killinchu"; $Host = "szlholdings-killinchu.hf.space"
(Invoke-RestMethod "https://huggingface.co/api/spaces/$Space") | Select-Object sha, @{n='stage';e={$_.runtime.stage}}, lastModified
$Paths = (Invoke-RestMethod "https://$Host/api/killinchu/openapi.json").paths.PSObject.Properties.Name
"live openapi paths: $($Paths.Count)"
# Compare with what main declares (rough): count route decorators
gh api repos/szl-holdings/killinchu/contents/serve.py --jq .content | % { [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($_)) } | Select-String '@app\.(get|post|put|delete)\(' | Measure-Object''',
    fix=r'''# Factory rebuild discards the cached image layers. Needs a write token for the org.
$Tok = Read-Host -AsSecureString "HF write token"
$H = @{ Authorization = "Bearer " + [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Tok)) }
Invoke-RestMethod -Method Post -Headers $H "https://huggingface.co/api/spaces/$Space/restart?factory=true"
Remove-Variable Tok, H
# Then poll (transient 000/5xx during rebuild is egress, not a crashed app — retry 3-6x)
1..12 | % { Start-Sleep 30; try { (Invoke-WebRequest -UseBasicParsing "https://$Host/healthz" -TimeoutSec 15).StatusCode } catch { "wait" } }''',
    verify=r'''(Invoke-RestMethod "https://$Host/api/killinchu/openapi.json").paths.PSObject.Properties.Name.Count''',
    notes="Diagnosis rule from KNOWN_GOTCHAS #9: 404 on a route whose code exists on main => check the deployed openapi path count against a local repro BEFORE suspecting a runtime exception. A failing register() leaves `NOT registered:` + traceback in Space logs; a clean boot with missing routes is a stale deploy. The HF Space git repo is distinct from GitHub main — a merge does not deploy by itself; the publisher lane does.",
    sources=["https://github.com/szl-holdings/killinchu/blob/main/KNOWN_GOTCHAS.md"],
)

add(
    id="hf-space-config-error",
    title="Space shows CONFIG_ERROR after a deploy — README front matter was overwritten",
    tags=["huggingface", "space", "readme", "front-matter", "reusable-hf-deploy"],
    surface="huggingface",
    severity="high",
    symptom="Space stage `CONFIG_ERROR`; the Space README.md lost its YAML block (`sdk: docker`, `app_port`, `title`). Root cause tracked in `.github#193`: `reusable-hf-deploy` with `include-readme:false` still let a Dockerfile-derived README overwrite the card.",
    diagnose=r'''$Space = "SZLHOLDINGS/<space>"
$Readme = Invoke-RestMethod "https://huggingface.co/spaces/$Space/raw/main/README.md"
if ($Readme -notmatch '(?s)^---\s*\n.*?\nsdk:\s*\w+') { "FRONT MATTER MISSING" } else { ($Readme -split "`n")[0..12] -join "`n" }''',
    fix=r'''# Restore the card header from the GitHub source (space/README.md or the repo README with HF block), via the HF commit API.
$Tok = Read-Host -AsSecureString "HF write token"
$H = @{ Authorization = "Bearer " + [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Tok)) }
$Header = @"
---
title: <Title>
emoji: 🛡️
colorFrom: gray
colorTo: red
sdk: docker
app_port: 7860
pinned: false
---
"@
$Body = $Header + "`n" + ($Readme -replace '(?s)^---.*?---\s*', '')
# hf CLI does the multipart commit for you:
$Tmp = Join-Path $env:TEMP "README.md"; Set-Content -LiteralPath $Tmp -Value $Body -Encoding UTF8 -NoNewline
hf upload $Space $Tmp README.md --repo-type space --commit-message "fix(card): restore Space front matter"
Remove-Variable Tok, H''',
    verify=r'''(Invoke-RestMethod "https://huggingface.co/api/spaces/$Space").runtime.stage''',
    notes="Durable fix lives in the deployer: the Space card is a contract the publish lane must preserve (hatun-mcp#58 was the proximate recovery). If a repo's lane keeps clobbering the card, it is not using the canonical `reusable-hf-deploy` inputs correctly.",
    sources=["https://github.com/szl-holdings/.github/issues/193", "https://github.com/szl-holdings/hatun-mcp/pull/58"],
)

add(
    id="hf-space-paused-or-sleeping",
    title="Free-tier Space paused or sleeping — restart it, then re-probe root and /healthz",
    tags=["huggingface", "space", "restart", "free-tier"],
    surface="huggingface",
    severity="medium",
    symptom="Space page shows Paused/Sleeping; `*.hf.space` root returns 503 or a Hub placeholder; estate monitors mark it not operational (the Living Constellation Operator fails closed with REPAIR_FAILED).",
    diagnose=r'''$Space = "SZLHOLDINGS/holographic"
(Invoke-RestMethod "https://huggingface.co/api/spaces/$Space").runtime | Select-Object stage, hardware''',
    fix=r'''$Tok = Read-Host -AsSecureString "HF write token"
$H = @{ Authorization = "Bearer " + [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Tok)) }
Invoke-RestMethod -Method Post -Headers $H "https://huggingface.co/api/spaces/$Space/restart"
Remove-Variable Tok, H''',
    verify=r'''$Sub = ($Space -replace '/','-').ToLower()
1..8 | % { Start-Sleep 20; try { (Invoke-WebRequest -UseBasicParsing "https://$Sub.hf.space/" -TimeoutSec 15).StatusCode } catch { "wait" } }''',
    notes="Static Spaces live at `https://<org>-<name>.static.hf.space/`, not `.hf.space` — a 404 at `.hf.space` for a static Space is expected, not an outage (prove-it, governed-receipt-verifier, szl-bench-suite, szl-forge-lab, szl-brand-campaign, foundation-confirmation-v2).",
    sources=[],
)

add(
    id="hf-space-dockerfile-copy",
    title="New organ/module 404s on the Space although the file synced — Dockerfile COPY discipline",
    tags=["huggingface", "space", "dockerfile", "killinchu", "a11oy", "organs"],
    surface="huggingface",
    severity="medium",
    symptom="A new `szl_<name>.py` organ is in the Space repo but its endpoint returns 404; the image never contained the file because the live Space Dockerfile has per-file `COPY` lines and the new one was never added.",
    diagnose=r'''$Space = "SZLHOLDINGS/killinchu"
$Df = Invoke-RestMethod "https://huggingface.co/spaces/$Space/raw/main/Dockerfile"
$Df -split "`n" | Select-String '^\s*COPY\s+szl_' | % { $_.Line.Trim() }''',
    fix=r'''# Add the COPY line to the LIVE Space Dockerfile (it diverges from the GitHub Dockerfile by design):
#   COPY szl_<name>.py ./
# Commit via hf CLI, then factory rebuild (see hf-space-stale-image).
$Tmp = Join-Path $env:TEMP "Dockerfile"; Set-Content -LiteralPath $Tmp -Value ($Df.TrimEnd() + "`nCOPY szl_<name>.py ./`n") -Encoding ASCII -NoNewline
hf upload $Space $Tmp Dockerfile --repo-type space --commit-message "build: COPY szl_<name>.py into image" ''',
    verify=r'''Invoke-RestMethod "https://szlholdings-killinchu.hf.space/api/killinchu/v1/<name>/health" ''',
    notes="Two more killinchu gotchas that crashed the Space before: the serve.py register block must write to `sys.stderr`, never `_frontier_sys` (undefined alias — wave 13 crash); and never `from __future__ import annotations` in files that define FastAPI routes or Pydantic models.",
    sources=["https://github.com/szl-holdings/killinchu/blob/main/KNOWN_GOTCHAS.md"],
)

add(
    id="hf-ecosystem-manifest-drift",
    title="a11oy 'HF Ecosystem manifest drift' is red — regenerate the manifest, open the candidate PR",
    tags=["huggingface", "a11oy", "manifest", "drift", "ci"],
    surface="huggingface",
    severity="medium",
    symptom="`HF Ecosystem manifest drift` fails on a11oy main after Hub counts change (e.g. 50/35/33). The collector prints a candidate manifest with `autoMerge:false, branchCreated:false` and exits 1.",
    diagnose=r'''$Run = gh run list --repo szl-holdings/a11oy --workflow "HF Ecosystem manifest drift" --limit 1 --json databaseId,conclusion,url --jq '.[0]'
$Run
gh run view ($Run | ConvertFrom-Json).databaseId --repo szl-holdings/a11oy --log 2>$null | Select-String '"counts"' | Select-Object -Last 1''',
    fix=r'''$Root = (Resolve-Path -LiteralPath "$HOME\src\a11oy").Path; Set-Location -LiteralPath $Root
git fetch origin; git checkout -b chore/hf-manifest-refresh origin/main
# the collector script is the one the workflow calls; run it the same way (see .github/workflows for the exact entrypoint)
Get-Content .github\workflows\hf-ecosystem-manifest-drift.yml | Select-String "run:|python" | Select-Object -First 12
python scripts\hf_ecosystem_manifest.py --write docs\huggingface-ecosystem-manifest.json   # adjust to the entrypoint printed above
git add docs\huggingface-ecosystem-manifest.json
git commit -s -m "chore(hf): refresh ecosystem manifest to observed Hub inventory"
git push -u origin chore/hf-manifest-refresh
gh pr create --repo szl-holdings/a11oy --fill --body-file ..\szl-ops-runbook\templates\pr-body.md''',
    verify=r'''gh run list --repo szl-holdings/a11oy --workflow "HF Ecosystem manifest drift" --limit 1 --json conclusion''',
    notes="The manifest is source-pinned on purpose: the org profile and Hub card link to a specific a11oy commit of this file. Refreshing it is a normal PR, not an emergency; the red run is the drift detector doing its job.",
    sources=["https://github.com/szl-holdings/a11oy/actions/runs/36796144190"],
)

add(
    id="a11oy-parity-single-writer",
    title="a11oy PRs fail 'Protected base matches immutable HF repository' / 'single-writer guard' / 'Shared source files in sync with killinchu'",
    tags=["a11oy", "killinchu", "huggingface", "parity", "single-writer", "required-check"],
    surface="github",
    severity="high",
    symptom="One or more of: `Protected base matches immutable HF repository`, `canonical HF single-writer guard (stdlib, network-free)`, `Shared source files in sync with killinchu` red on an a11oy PR (#2386, #2360, #2318).",
    diagnose=r'''$Repo = "szl-holdings/a11oy"; $Pr = 2360
gh pr checks $Pr --repo $Repo | Select-String "HF repository|single-writer|killinchu"
# Which shared files differ from killinchu?
$Root = (Resolve-Path -LiteralPath "$HOME\src\a11oy").Path; Set-Location -LiteralPath $Root
git fetch origin; git checkout (gh pr view $Pr --repo $Repo --json headRefName --jq .headRefName)
Get-Content .github\workflows\*.yml | Select-String "shared_source_sync|SHARED_FILES|killinchu" | Select-Object -First 8''',
    fix=r'''# Parity/single-writer gates compare the PR base to the immutable Hub revision: a stale base fails even with a perfect diff.
gh pr update-branch $Pr --repo $Repo --rebase
# Shared-source drift: the shared modules are owned by szl-substrate / killinchu; re-copy from the owner rather than editing the a11oy copy.
# (the sync script prints the exact file list)
python scripts\check_shared_source_sync.py --fix 2>$null; git status --short''',
    verify=r'''gh pr checks $Pr --repo $Repo | Select-String "HF repository|single-writer|killinchu" ''',
    notes="Issue a11oy#1615 recorded a logically unsatisfiable pair of pre-merge checks (one requiring a mirrored file to change, one requiring byte identity with main); the durable gate is a post-merge push-to-main parity check. Canonical sync owns the HF writes — never hand-push the a11oy Space while a PR is open.",
    sources=["https://github.com/szl-holdings/a11oy/issues/1615", "https://github.com/szl-holdings/a11oy/pull/1802"],
)

add(
    id="hf-constellation-operator-repair-failed",
    title="'HF Living Constellation Operator' red: 'One or more public Spaces were not proven operational'",
    tags=["huggingface", ".github", "scheduler", "spaces", "fleet"],
    surface="huggingface",
    severity="medium",
    symptom="Scheduled `.github` lane fails with `REPAIR_FAILED: 1` and the uploaded exact fleet receipt names the Space(s) that did not answer.",
    diagnose=r'''$Run = gh run list --repo szl-holdings/.github --workflow "HF Living Constellation Operator" --limit 1 --json databaseId --jq '.[0].databaseId'
$Dir = Join-Path $env:TEMP "fleet-$Run"; gh run download $Run --repo szl-holdings/.github --dir $Dir 2>$null
Get-ChildItem $Dir -Recurse -Filter *.json | % { (Get-Content $_.FullName | ConvertFrom-Json).spaces | Where-Object { -not $_.operational } | Format-Table id, stage, http, reason -AutoSize }''',
    fix=r'''# Usually one Space asleep or rebuilding: restart it (hf-space-paused-or-sleeping), then re-run the operator lane
gh workflow run "HF Living Constellation Operator" --repo szl-holdings/.github''',
    verify=r'''gh run list --repo szl-holdings/.github --workflow "HF Living Constellation Operator" --limit 1 --json conclusion''',
    notes="This lane fails closed by design; a 'green' that hides one dead Space would violate doctrine. Three consecutive scheduled receipts at 18/18 is the bar the Constellation project used for 'operational'.",
    sources=["https://github.com/szl-holdings/.github/actions/runs/36791432977", "https://github.com/szl-holdings/szl-constellation/issues/4"],
)

add(
    id="hf-token-rotation",
    title="Rotate Hugging Face tokens safely — revoke, mint fine-grained, re-seat, re-run",
    tags=["huggingface", "token", "rotation", "secrets", "security"],
    surface="huggingface",
    severity="high",
    symptom="A token was exposed, expired, or you are consolidating many tokens into one (the 2026-09-30 rotation: revoke hf_nGHC… and hf_rpzm…, keep one fresh token).",
    diagnose=r'''hf auth whoami 2>&1 | Select-Object -First 8
gh secret list --org szl-holdings --json name --jq '[.[].name]' ''',
    fix=r'''# 1. In the Hub UI: Settings -> Access Tokens -> revoke old; create ONE fine-grained token:
#    repos: write on SZLHOLDINGS/* that CI publishes; no user-scope; name it by purpose + date.
# 2. Local login (browser flow; token never printed)
hf auth login --force
# 3. Seat it for CI (see hf-deploy-400-401-token) — org secret HF_TOKEN (+ HF_ORG_TOKEN alias where used)
# 4. Re-run the lanes that failed with 400/401.''',
    verify=r'''hf auth whoami; gh run list --repo szl-holdings/yarqa --workflow "HF Space deploy" --limit 1 --json conclusion''',
    notes="Prefer trusted publishing / OIDC where a lane supports it over long-lived tokens. Never paste a token into a chat, issue, or PR body; the runbook blocks read it with Read-Host -AsSecureString for that reason.",
    sources=["https://github.com/szl-holdings/szl-doctrine/blob/main/FOUNDER_SECRETS_RUNBOOK.md"],
)
