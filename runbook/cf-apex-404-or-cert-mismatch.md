---
id: cf-apex-404-or-cert-mismatch
title: "a-11-oy.com apex 404 / www certificate mismatch — custom-domain binding, keep the orange cloud"
surface: domains
severity: high
tags: [cloudflare, dns, custom-domain, huggingface, tls, apex, www]
last_verified: 2026-10-01
---
# a-11-oy.com apex 404 / www certificate mismatch — custom-domain binding, keep the orange cloud

## Symptom
Apex serves an HF edge 404 or a TLS name mismatch while the backing Space `szlholdings-a11oy.hf.space` is healthy (incidents 2026-09-01 and 2026-09-30, a11oy#2389). Space health and custom-domain health are separate claims.

## Diagnose (PowerShell 5.1)
```powershell
foreach ($u in "https://a-11-oy.com/","https://www.a-11-oy.com/","https://szlholdings-a11oy.hf.space/healthz","https://holdings.a-11-oy.com/") {
  try { $r = Invoke-WebRequest -UseBasicParsing -Method Head $u -TimeoutSec 15; "{0,-45} {1} server={2}" -f $u, $r.StatusCode, $r.Headers.Server } catch { "{0,-45} {1}" -f $u, $_.Exception.Message.Substring(0,[Math]::Min(60,$_.Exception.Message.Length)) }
}
Resolve-DnsName a-11-oy.com -Type A | Select-Object Name, IPAddress
Resolve-DnsName www.a-11-oy.com -Type CNAME -ErrorAction SilentlyContinue | Select-Object Name, NameHost
# HF side: provider stage for the custom domain (needs org token)
# (Invoke-RestMethod -Headers @{Authorization="Bearer <token>"} https://huggingface.co/api/spaces/SZLHOLDINGS/a11oy).runtime.domains
```

## Fix
```powershell
# Rules that held through both incidents:
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
Remove-Variable Tok, H
```

## Verify
```powershell
(Invoke-WebRequest -UseBasicParsing https://a-11-oy.com/ -TimeoutSec 15).StatusCode; (Invoke-WebRequest -UseBasicParsing -MaximumRedirection 0 https://www.a-11-oy.com/ -TimeoutSec 15 -ErrorAction SilentlyContinue).StatusCode
```

## Notes
a11oy.com (no dashes) is an unrelated third-party store — never link it. a11oy.net zone id is 6893093cd089c9994349bc16b0906006 (GitHub Pages: 4x A 185.199.108-111.153 + www CNAME szl-holdings.github.io). Public 200 on the proxied apex beats a green HF domain row; the Spaces health endpoint keeps the row DEGRADED until the provider says READY — that is honest, leave it.

## Sources
- https://github.com/szl-holdings/a11oy/blob/main/docs/SPACES_HEALTH_OPERATIONS.md
- https://github.com/szl-holdings/a11oy/issues/1497
