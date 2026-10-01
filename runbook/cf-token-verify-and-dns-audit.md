---
id: cf-token-verify-and-dns-audit
title: "Verify a Cloudflare token and dump both zones' DNS — before any write"
surface: domains
severity: medium
tags: [cloudflare, dns, token, audit, a11oy.net, a-11-oy.com]
last_verified: 2026-10-01
---
# Verify a Cloudflare token and dump both zones' DNS — before any write

## Symptom
A connector or script reports HTTP 400 code 6003 / 6103 (`Invalid format for X-Auth-Key header`) or 403; you need to know whether the token is live and what the zones hold right now.

## Diagnose (PowerShell 5.1)
```powershell
$Tok = Read-Host -AsSecureString "Cloudflare API token"
$H = @{ Authorization = "Bearer " + [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Tok)) }
(Invoke-RestMethod -Headers $H https://api.cloudflare.com/client/v4/user/tokens/verify).result | Select-Object status, expires_on
$Zones = @{ "a-11-oy.com" = "27911fb3d5ed874fdd4e844ed7f5e248"; "a11oy.net" = "6893093cd089c9994349bc16b0906006" }
foreach ($z in $Zones.GetEnumerator()) {
  "== $($z.Key)"
  (Invoke-RestMethod -Headers $H "https://api.cloudflare.com/client/v4/zones/$($z.Value)/dns_records?per_page=200").result | Sort-Object type, name | Format-Table type, name, content, proxied, ttl -AutoSize
  (Invoke-RestMethod -Headers $H "https://api.cloudflare.com/client/v4/zones/$($z.Value)/dnssec").result | Select-Object status
}
Remove-Variable Tok, H
```

## Fix
```powershell
# Token says anything but "active": regenerate in the Cloudflare dashboard with exactly Zone:DNS:Edit + Zone:Zone:Read on the two zones.
# Export a rollback bundle BEFORE writing anything:
# Invoke-RestMethod -Headers $H "https://api.cloudflare.com/client/v4/zones/<zone>/dns_records/export" | Set-Content -LiteralPath "$HOME\cf-<zone>-$(Get-Date -f yyyyMMdd).bind" -Encoding ASCII
```

## Verify
```powershell
Resolve-DnsName a11oy.net -Type NS | Select-Object NameHost; Resolve-DnsName a-11-oy.com -Type NS | Select-Object NameHost
```

## Notes
Both zones validated DNSSEC (DS at parent) as of 2026-10-01. One writer at a time: concurrent DNS edits from two sessions produced conflicting observations on 2026-08-31 — finish one change, read it back, then start the next.

## Sources
- https://github.com/szl-holdings/szl-v14/blob/main/OPERATOR_PACKET.md
