# SZL ops runbook (private)

<!-- szl:header v1 -->
<!-- Native identity: szl-brand@4309f6fce89179331b0b3ed8c99494e76c5be256; Orbit v2 icon. -->
<p>
  <a href="https://github.com/szl-holdings">
    <img src="https://raw.githubusercontent.com/szl-holdings/szl-brand/4309f6fce89179331b0b3ed8c99494e76c5be256/kit/logos/orbit-v2/suite/szl-icon-32.svg" alt="SZL Holdings — Orbit v2" width="32" height="32" />
  </a>
</p>

**Control before action. Evidence after.**

[Product](https://a-11-oy.com) · [Proof](https://a11oy.net) · [GitHub organization](https://github.com/szl-holdings)
<!-- /szl:header -->

Recovery commands Stephen actually uses, one search away. Every entry is a symptom → diagnose → fix → verify unit written for Windows PowerShell 5.1 in an elevated console with no prior shell state. Tokens are read with `Read-Host -AsSecureString` and never echoed, logged, or committed.

## Three ways to search

1. **Browser** — open `site/index.html` (no network needed). Type a symptom (`530`, `400 Bad Request`, `BEHIND`, `provenance`, `CONFIG_ERROR`, `stale image`). `/` focuses search, `Esc` clears, every block has a copy button. The same page is deployed privately from this repo.
2. **Terminal** — dot-source the finder once, then search:
   ```powershell
   . .\tools\Find-Fix.ps1
   Find-Fix 530                         # list matches
   Find-Fix "400 Bad Request" -Show     # print best match in full
   Find-Fix provenance -Copy            # copy its FIX block to the clipboard
   ```
3. **ripgrep** — `rg -i "530|1033" runbook/` or `rg -l provenance runbook/`.

## Layout

```
runbook/<id>.md        one entry per failure mode (front matter + Symptom/Diagnose/Fix/Verify/Notes/Sources)
site/index.html        searchable single page; site/runbook.json is the index it reads
tools/entries_*.py     the source of every entry (edit here, then build)
tools/build.py         regenerates runbook/, site/, INDEX.md
tools/Find-Fix.ps1     terminal search
tools/unblocker.py     weekday unblocker board generator (stalled PRs → ranked fixes mapped to entries)
templates/pr-body.md   the seven headings szl/provenance requires
templates/org-profile-README.md   verified-passing org profile (front-door + router + estate-alignment validators green)
INDEX.md               table of all entries
```

## Adding an entry

Append an `add(...)` block to the matching `tools/entries_*.py` (A: GitHub/PR flow · B: Hugging Face · C: domains, own-metal, org profile, local, control plane), then:

```powershell
python tools\build.py
git add -A; git commit -s -m "runbook: add <id>"; git push
```

Rules: real commands only (no placeholders you have not run), name the failure by its observable symptom, include the exact check or workflow name, and state what the fix does **not** prove. Dated observations stay dated.

## Honesty boundary

This runbook records how to restore surfaces and gates. It does not promote models, bypass required checks, or relabel UNAVAILABLE as green. Where a fix needs the owner (shell on the own-metal box, org-admin permission, token minting), the entry says so.

Built from the 2026-10-01 estate audit: 132 repositories (103 active), 24 open PRs, 709 default-branch workflows scanned (26 red), 50 models / 35 datasets / 33 Spaces, both domains behind Cloudflare with DNSSEC.
