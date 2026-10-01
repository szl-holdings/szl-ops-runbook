---
id: gh-pages-custom-domain
title: "GitHub Pages site (a11oy.net, dev.a-11-oy.com) not serving or wrong cert — CNAME file + DNS + Pages config"
surface: domains
severity: medium
tags: [github-pages, dns, a11oy.net, dev, custom-domain]
last_verified: 2026-10-01
---
# GitHub Pages site (a11oy.net, dev.a-11-oy.com) not serving or wrong cert — CNAME file + DNS + Pages config

## Symptom
a11oy.net (repo `a11oy-net`) or dev.a-11-oy.com (repo `szl-platform`, branch gh-pages) returns 404, a GitHub 'There isn't a GitHub Pages site here', or a certificate for the wrong name.

## Diagnose (PowerShell 5.1)
```powershell
gh api repos/szl-holdings/a11oy-net/pages --jq '{cname,status,https_enforced,source}'
gh api repos/szl-holdings/szl-platform/pages --jq '{cname,status,https_enforced,source}'
Resolve-DnsName dev.a-11-oy.com -Type CNAME | Select-Object NameHost
Resolve-DnsName a11oy.net -Type A | Select-Object IPAddress
```

## Fix
```powershell
# Pages needs all three to agree: (1) DNS -> szl-holdings.github.io (CNAME, DNS-only for subdomains) or the 4 GitHub A records for an apex,
# (2) a CNAME file at the published root containing exactly the hostname, (3) the repo Pages setting with that custom domain.
gh api -X PUT repos/szl-holdings/a11oy-net/pages -f cname=a11oy.net -F https_enforced=true
# Re-request the certificate after a DNS fix:
gh api -X POST repos/szl-holdings/a11oy-net/pages/builds
```

## Verify
```powershell
(Invoke-WebRequest -UseBasicParsing https://a11oy.net/health.json).StatusCode; (Invoke-WebRequest -UseBasicParsing https://dev.a-11-oy.com/).Headers.Server
```

## Notes
Only one custom domain per Pages site; a second one on the same org site fails (that is why dev.a-11-oy.com moved to the szl-platform gh-pages branch). The org SHA-pin rule forbids the official Pages actions, so the pages-sync workflow pushes the built tree to gh-pages itself.

## Sources
- https://github.com/szl-holdings/szl-platform/blob/main/docs/OPERATOR_PACKET.md
