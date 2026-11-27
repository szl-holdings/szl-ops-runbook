// szl-outside-monitor: free, no-new-account black-box monitor on the existing Cloudflare account.
// Probes public SZL endpoints on a cron, emails the on-call address (ONCALL.md) through
// Cloudflare Email Routing `send_email` when a target changes state, and sends one daily heartbeat.
// No secrets: the destination must already be a VERIFIED Email Routing destination address.
// Independence note (DEADMAN_DESIGN.md rule 1): this runs on Cloudflare Workers, so it does not
// cover a Cloudflare-wide outage. The daily heartbeat is the dead-man's cover: no heartbeat email
// by ~7:30 AM ET means the monitor itself is down.

export const TARGETS = [
  // ok(status): what counts as UP. 402 is the x402 paywall answering, i.e. the origin path is alive.
  { name: "inference", url: "https://inference.a-11-oy.com/v1/models", ok: (s) => s === 200 || s === 401 || s === 402 },
  // inference /health is 404 on the current origin (hatun :8081, Nov 26); /v1/models above is the probe.
  // mcp: /healthz is the paging probe (readyz is 200 since Nov 26 but stays out of paging to keep noise low).
  { name: "mcp", url: "https://mcp.a-11-oy.com/healthz", ok: (s) => s === 200 },
  { name: "alert-relay", url: "https://ntfy.a11oy.net/.well-known/szl-worker-revision", ok: (s) => s === 200 },
  // a11oy apex: /healthz is WAF-skipped. One GET per 5 min (the old /api/a11oy/v1/health probe was heavier).
  { name: "a11oy-apex", url: "https://a-11-oy.com/healthz", ok: (s) => s === 200 },
  { name: "a11oy-net", url: "https://a11oy.net/", ok: (s) => s === 200 },
  // api.a-11-oy.com is deliberately absent: no origin (404 catch-all on Nov 26); re-add after the DNS decision.
];

export async function probe(target, fetchImpl = fetch, timeoutMs = 10000) {
  const started = Date.now();
  try {
    const res = await fetchImpl(target.url, {
      method: "GET",
      redirect: "manual",
      headers: { "User-Agent": "szl-outside-monitor/1" },
      signal: AbortSignal.timeout(timeoutMs),
    });
    const status = res.status;
    try { await res.body?.cancel(); } catch {}
    return { name: target.name, status, up: target.ok(status), ms: Date.now() - started, error: null };
  } catch (err) {
    const error = err && err.name === "TimeoutError" ? "timeout" : String(err && err.name || "error");
    return { name: target.name, status: 0, up: false, ms: Date.now() - started, error };
  }
}

// Returns the targets whose UP/DOWN state differs from the previous run (first run: only DOWN ones).
export function transitions(prev, results) {
  return results.filter((r) => {
    const before = prev ? prev[r.name] : undefined;
    return before === undefined ? !r.up : before !== r.up;
  });
}

export function buildMime({ from, to, subject, text, now = new Date() }) {
  const safe = (s) => String(s).replace(/[\r\n]+/g, " ");
  const id = `<${now.getTime()}.${Math.random().toString(36).slice(2)}@${from.split("@")[1]}>`;
  return [
    `From: SZL outside monitor <${safe(from)}>`,
    `To: ${safe(to)}`,
    `Subject: ${safe(subject)}`,
    `Date: ${now.toUTCString()}`,
    `Message-ID: ${id}`,
    "MIME-Version: 1.0",
    "Content-Type: text/plain; charset=utf-8",
    "Content-Transfer-Encoding: 8bit",
    "",
    text,
  ].join("\r\n");
}

export function summarize(results) {
  return results.map((r) => `${r.up ? "UP  " : "DOWN"} ${r.name.padEnd(16)} status=${r.status} ${r.ms}ms${r.error ? " err=" + r.error : ""}`).join("\n");
}

async function send(env, subject, text) {
  const { EmailMessage } = await import("cloudflare:email");
  const raw = buildMime({ from: env.MONITOR_FROM, to: env.MONITOR_TO, subject, text });
  await env.ALERT_EMAIL.send(new EmailMessage(env.MONITOR_FROM, env.MONITOR_TO, raw));
}

export async function run(env, { heartbeat = false, fetchImpl = fetch, sendImpl = send } = {}) {
  const results = await Promise.all(TARGETS.map((t) => probe(t, fetchImpl)));
  const prevRaw = env.STATE ? await env.STATE.get("last") : null;
  const prev = prevRaw ? JSON.parse(prevRaw) : null;
  const changed = transitions(prev, results);
  const next = Object.fromEntries(results.map((r) => [r.name, r.up]));
  if (env.STATE && JSON.stringify(next) !== prevRaw) await env.STATE.put("last", JSON.stringify(next));
  const down = results.filter((r) => !r.up);
  const body = summarize(results) + "\n\nRunbook: szl-ops-runbook monitor/README.md. TEST label appears only on manual tests.";
  if (changed.length) {
    const verb = changed.map((r) => `${r.name} ${r.up ? "RECOVERED" : "DOWN"}`).join(", ");
    await sendImpl(env, `[SZL monitor] ${verb}`, body);
  }
  if (heartbeat) {
    await sendImpl(env, `[SZL monitor] daily heartbeat: ${down.length ? down.length + " down" : "all up"}`, body);
  }
  return { results, changed: changed.map((r) => r.name), heartbeat };
}

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(run(env, { heartbeat: event.cron === env.HEARTBEAT_CRON }));
  },
  // No public trigger: fetch only reports that the Worker exists (no probing, no email).
  async fetch() {
    return new Response("szl-outside-monitor\n", { status: 200, headers: { "content-type": "text/plain" } });
  },
};
