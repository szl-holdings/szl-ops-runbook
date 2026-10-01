# SZL ops runbook — index

33 entries · last verified 2026-10-01

| id | surface | severity | title |
|---|---|---|---|
| [`a11oy-parity-single-writer`](runbook/a11oy-parity-single-writer.md) | github | high | a11oy PRs fail 'Protected base matches immutable HF repository' / 'single-writer guard' / 'Shared source files in sync with killinchu' |
| [`codeql-triage`](runbook/codeql-triage.md) | github | medium | CodeQL alerts — list, triage, and close with evidence |
| [`dco-bot-prs`](runbook/dco-bot-prs.md) | github | low | DCO blocks a Dependabot or bot PR — solo-build policy, not an admin bypass |
| [`deadman-census-red`](runbook/deadman-census-red.md) | github | medium | 'Estate dead-man supervisor' / 'Estate readiness evidence' red — census fails closed on completeness |
| [`dependabot-updates-red`](runbook/dependabot-updates-red.md) | github | low | 'Dependabot Updates' workflow is red — read the updater error, fix the lockfile, or ignore the ecosystem |
| [`org-profile-validators`](runbook/org-profile-validators.md) | github | high | szl-holdings org profile red on Tests / SZL Router flagship alignment / estate alignment — required blocks and word budgets |
| [`pr-behind-main`](runbook/pr-behind-main.md) | github | medium | PR is BEHIND main — update the branch before anything else |
| [`pr-conflicting`](runbook/pr-conflicting.md) | github | medium | PR is CONFLICTING (DIRTY) — rebase and resolve, or close as net-zero |
| [`pr-control-plane-effect`](runbook/pr-control-plane-effect.md) | github | high | 'Static control-plane effect boundary' fails — workflow/script change outside the admitted grammar |
| [`pr-exact-head-provenance`](runbook/pr-exact-head-provenance.md) | github | high | 'Exact-head organization provenance' fails — PR is draft, behind, or forked |
| [`pr-merge-conveyor`](runbook/pr-merge-conveyor.md) | github | medium | Merge every green PR org-wide (squash), skip HOLD, log the rest — one block |
| [`pr-provenance-headings`](runbook/pr-provenance-headings.md) | github | high | 'szl/provenance' fails — PR body is missing the seven policy headings |
| [`red-workflows-scan`](runbook/red-workflows-scan.md) | github | medium | Which workflows are red on main right now, org-wide — the one-block scan |
| [`secret-health-unavailable`](runbook/secret-health-unavailable.md) | github | low | secret-health reports UNAVAILABLE — qillqaq App permission, not a new PAT |
| [`security-gate-platform`](runbook/security-gate-platform.md) | github | high | 'Security Gate (blocking)' or 'Dependency Vulnerability Scan' red on platform — HIGH CVE in the pnpm tree |
| [`hf-constellation-operator-repair-failed`](runbook/hf-constellation-operator-repair-failed.md) | huggingface | medium | 'HF Living Constellation Operator' red: 'One or more public Spaces were not proven operational' |
| [`hf-deploy-400-401-token`](runbook/hf-deploy-400-401-token.md) | huggingface | high | HF Space/dataset deploy fails 400 Bad Request or 401 — HF_TOKEN missing or rotated |
| [`hf-ecosystem-manifest-drift`](runbook/hf-ecosystem-manifest-drift.md) | huggingface | medium | a11oy 'HF Ecosystem manifest drift' is red — regenerate the manifest, open the candidate PR |
| [`hf-space-config-error`](runbook/hf-space-config-error.md) | huggingface | high | Space shows CONFIG_ERROR after a deploy — README front matter was overwritten |
| [`hf-space-dockerfile-copy`](runbook/hf-space-dockerfile-copy.md) | huggingface | medium | New organ/module 404s on the Space although the file synced — Dockerfile COPY discipline |
| [`hf-space-paused-or-sleeping`](runbook/hf-space-paused-or-sleeping.md) | huggingface | medium | Free-tier Space paused or sleeping — restart it, then re-probe root and /healthz |
| [`hf-space-stale-image`](runbook/hf-space-stale-image.md) | huggingface | high | Space reports RUNNING on the new commit but serves old code (routes 404) — factory rebuild |
| [`hf-token-rotation`](runbook/hf-token-rotation.md) | huggingface | high | Rotate Hugging Face tokens safely — revoke, mint fine-grained, re-seat, re-run |
| [`cf-apex-404-or-cert-mismatch`](runbook/cf-apex-404-or-cert-mismatch.md) | domains | high | a-11-oy.com apex 404 / www certificate mismatch — custom-domain binding, keep the orange cloud |
| [`cf-token-verify-and-dns-audit`](runbook/cf-token-verify-and-dns-audit.md) | domains | medium | Verify a Cloudflare token and dump both zones' DNS — before any write |
| [`estate-probe`](runbook/estate-probe.md) | domains | low | Probe every public surface in one pass — the expected codes |
| [`gh-pages-custom-domain`](runbook/gh-pages-custom-domain.md) | domains | medium | GitHub Pages site (a11oy.net, dev.a-11-oy.com) not serving or wrong cert — CNAME file + DNS + Pages config |
| [`cf-tunnel-530`](runbook/cf-tunnel-530.md) | own-metal | high | gpu / gateway / meter / meter2 .a-11-oy.com return 530 (error 1033) — cloudflared is down on the box |
| [`own-metal-services`](runbook/own-metal-services.md) | own-metal | medium | Ollama / joule exporter / LiteLLM down behind a live tunnel (502/503/404) — restart the local stack |
| [`model-gates-not-promotable`](runbook/model-gates-not-promotable.md) | models | medium | szl-typesafe-triage: receipt verification red, 11 of 12 gates — publish evidence, do not promote |
| [`gh-auth-and-rate-limit`](runbook/gh-auth-and-rate-limit.md) | local | medium | gh says 401/403 or 'rate limit exceeded' — refresh auth, check scopes, wait honestly |
| [`pnpm-web-build-fails-locally`](runbook/pnpm-web-build-fails-locally.md) | local | medium | a11oy / platform web monorepo won't build in a fresh sandbox — unwired pnpm workspace deps |
| [`ps51-gotchas`](runbook/ps51-gotchas.md) | local | medium | Windows PowerShell 5.1 gotchas that have eaten whole sessions |
