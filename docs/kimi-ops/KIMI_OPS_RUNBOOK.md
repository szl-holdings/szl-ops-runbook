# Kimi-Ops Lane Runbook (2026-11-20)

Standing CTO operator: Kimi (kimi-k3.1-pro:cloud via Ollama on estate laptop).
Charter: fail-closed, measured receipts only, never fabricate, secrets never enter model context (local harness scripts hold secrets; receipts only return to the model), parallel lanes co-exist (attribute, never absorb; yield on owned work), owner gates absolute, never auto-publish the 5 private repos.

## Loop
- Sessions 1-4 transcripts included (charter handoff, mandate expansion, lap-2 frontier sweep adjudication, lap-3 re-adjudication).
- Queue v1.1: items 1-3 triaged (sentra BLOCKED_OWNER_GATE ghcr grant; szl-drift ALREADY_REMEDIATED; david-leads BLOCKED_DEPLOYED_RUNTIME_404); item 4 CLOSED NO_CI_REQUIRED (frontier-54-runs/frontier-55-runs mirrors-by-design of HF system of record; pliny sandbox + estate-backup archives; szl-acoustic-research placeholder); items 5-6 blocked; 7-11 new planes (Snowflake bring-up, HF token gate, PyPI trustee, CF token, GHCR verify).

## Snowflake bring-up (Part A complete, Part B/C owner-gated)
- Isolated local venv + snowflake-connector-python 5.2.0; scaffold C:/SZL/snowflake/{config,sql,scripts,receipts,tests}.
- Config TEMPLATE only in this publication (placeholders). Real szl.ini stays DPAPI-local; never published.
- Selftest fail-closed (identity mismatch aborts; SELFTEST_NO_CONFIG receipt banked pre-credentials).
- Owner must provide: verified account identifier, username, auth method (prefer key-pair), role, warehouse, database/schema.

## Owner gates pending
GHCR Actions-access Write grants x3 (sentra/rosie/amaru package settings); PyPI Trusted Publisher (szl-evidence-core, publish-pypi.yml, environment pypi, rerun run 44599364585); Cloudflare Zone:Edit token; HF token (whoami-v2 anon = 401 this lap); Snowflake credentials via local entry script.

Publish gate: KIMI-OPS-PUBLISH-GATE (publish_gate receipt included). Merge of PRs NOT authorized until branch-protection policy measured.