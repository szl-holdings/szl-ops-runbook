# szl-outside-monitor

Free outside monitor on the existing Cloudflare account (no new account, no paid service).
Every 5 min it probes inference., api., mcp. (a-11-oy.com), the alert relay revision endpoint
(ntfy.a11oy.net) and the revenue-tracker route; it emails the ONCALL.md primary address
(`stephenlutar2@gmail.com`, already a verified Email Routing destination) when any target changes
UP/DOWN, plus one daily heartbeat at 12:30 UTC (7:30 AM ET). No heartbeat by ~8 AM ET = monitor is down.

Design source: Saywa production/deadman/DEADMAN_DESIGN.md. Limitation: it runs on Cloudflare,
so a Cloudflare-wide outage is covered only by the *missing* heartbeat.

## Test
`node --test test/index.test.mjs` (5 tests, no dependencies)

## Deploy (after merge to main; Stephen-approved D3, 2026-11-19)
1. `npx wrangler kv namespace create szl-outside-monitor-state` and put the id in wrangler.jsonc.
2. `npx wrangler deploy --config wrangler.jsonc --message <merge sha>`.
3. Manual TEST: `npx wrangler dev --test-scheduled` locally, or wait for the first cron.

## Rollback
- Stop all probes/emails: `npx wrangler triggers deploy` with `"crons": []`, or
  `npx wrangler delete --name szl-outside-monitor` (also delete the KV namespace).
- No other resource is touched.
