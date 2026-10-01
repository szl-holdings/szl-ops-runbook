---
id: estate-probe
title: "Probe every public surface in one pass — the expected codes"
surface: domains
severity: low
tags: [probe, status, domains, huggingface, monitoring]
last_verified: 2026-10-01
---
# Probe every public surface in one pass — the expected codes

## Symptom
You want the truth table for the estate before a demo, after a deploy, or when something feels off.

## Diagnose (PowerShell 5.1)
```powershell
$Targets = [ordered]@{
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
}
```

## Fix
```powershell
# Any DIFF maps to an entry: 530 -> cf-tunnel-530 · apex 404/TLS -> cf-apex-404-or-cert-mismatch · Space 5xx -> hf-space-paused-or-sleeping / hf-space-stale-image · Pages 404 -> gh-pages-custom-domain
```

## Verify
```powershell
# All rows 'ok' is the demo-ready state. Save the output with the date next to the receipt you are about to show.
```

## Notes
Snapshot 2026-10-01 01:10Z: every row ok except gpu/gateway/meter/meter2 = 530 (own-metal tunnel down). szlholdings.com has no working TLS and www.szlholdings.com does not resolve — known owner-level item, not part of the product estate.
