---
id: showcase-custom-domain
title: "showcase.a-11-oy.com — GitHub Pages for szl-showcase needs one Cloudflare CNAME (connector token broken)"
surface: domains
severity: medium
tags: [showcase, github-pages, cloudflare, dns, a-11-oy.com]
last_verified: 2026-10-01
---
# showcase.a-11-oy.com — GitHub Pages for szl-showcase needs one Cloudflare CNAME (connector token broken)

## Symptom
Repo szl-holdings/szl-showcase is public with Pages enabled (source main:/), CNAME file and Pages custom domain set to showcase.a-11-oy.com, but DNS has no record yet; the Cloudflare connector fails auth (code 9106), so the record must be created from the owner console. Until then the page is live at https://szl-showcase.pplx.app.

## Diagnose (PowerShell 5.1)
```powershell
gh api repos/szl-holdings/szl-showcase/pages --jq '{status,cname,https_enforced,protected_domain_state}'
Resolve-DnsName showcase.a-11-oy.com -Type CNAME -ErrorAction SilentlyContinue | Select-Object NameHost
```

## Fix
```powershell
$Tok = Read-Host -AsSecureString "Cloudflare API token (Zone:DNS:Edit on a-11-oy.com)"
$H = @{ Authorization = "Bearer " + [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Tok)); "Content-Type" = "application/json" }
$Zone = "27911fb3d5ed874fdd4e844ed7f5e248"
$Body = '{"type":"CNAME","name":"showcase","content":"szl-holdings.github.io","ttl":1,"proxied":false}'
Invoke-RestMethod -Method Post -Headers $H -Body $Body "https://api.cloudflare.com/client/v4/zones/$Zone/dns_records" | Select-Object -ExpandProperty result | Select-Object name, content, proxied
Remove-Variable Tok, H
# After GitHub provisions the certificate (minutes to an hour):
gh api -X PUT repos/szl-holdings/szl-showcase/pages -F https_enforced=true
```

## Verify
```powershell
(Invoke-WebRequest -UseBasicParsing https://showcase.a-11-oy.com/ -TimeoutSec 20).StatusCode
```

## Notes
DNS-only (grey cloud) is required while GitHub issues the certificate; it can be proxied afterwards if you want Cloudflare headers, but holdings.a-11-oy.com already works grey. Decide later whether holdings.a-11-oy.com (the older landing) redirects to showcase or the reverse — two landings is a duplicate surface under doctrine.

## Sources
- https://github.com/szl-holdings/szl-showcase
