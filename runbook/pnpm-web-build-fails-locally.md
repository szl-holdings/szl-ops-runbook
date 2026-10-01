---
id: pnpm-web-build-fails-locally
title: "a11oy / platform web monorepo won't build in a fresh sandbox — unwired pnpm workspace deps"
surface: local
severity: medium
tags: [pnpm, node, build, a11oy, platform, monorepo]
last_verified: 2026-10-01
---
# a11oy / platform web monorepo won't build in a fresh sandbox — unwired pnpm workspace deps

## Symptom
`pnpm install` or `pnpm -r build` fails with unresolved workspace packages, Node version mismatch (Node 24 expected), or Vite/typecheck errors that CI does not show.

## Diagnose (PowerShell 5.1)
```powershell
node -v; pnpm -v
$Root = (Resolve-Path -LiteralPath "$HOME\src\a11oy").Path; Set-Location -LiteralPath $Root
Get-Content pnpm-workspace.yaml; Get-Content package.json | ConvertFrom-Json | Select-Object -ExpandProperty engines
```

## Fix
```powershell
# Match CI exactly
corepack enable; corepack prepare pnpm@latest --activate
nvm use 24   # or fnm use 24
pnpm install --frozen-lockfile
pnpm -r --filter "./web/..." build
# a11oy's operational Hub surface is produced by the payload target, not by a dev server:
pnpm payload:huggingface
# doctrine demo:
pnpm test:doctrine
```

## Verify
```powershell
Get-ChildItem web\dist -Recurse -Filter index.html | Select-Object FullName
```

## Notes
a11oy is a TypeScript library workspace with a Python serving layer, not a Docker-first web app; treat `pnpm payload:huggingface` as the artifact. CI has a bundle-integrity guard (a11oy#718) for stale chunk 404s — if a Space shows a chunk 404, rebuild and republish rather than shimming.

## Sources
- https://github.com/szl-holdings/a11oy/pull/718
- https://github.com/szl-holdings/platform/pull/398
