import test from "node:test";
import assert from "node:assert/strict";
import { TARGETS, probe, transitions, buildMime, run } from "../src/index.mjs";

const fakeFetch = (map) => async (url) => {
  const v = map[url];
  if (v === "timeout") { const e = new Error("t"); e.name = "TimeoutError"; throw e; }
  return { status: v ?? 200, body: { cancel: async () => {} } };
};
const kv = () => { const m = new Map(); return { get: async (k) => m.get(k) ?? null, put: async (k, v) => m.set(k, v) }; };
const url = (n) => TARGETS.find((t) => t.name === n).url;
const T = (n) => TARGETS.find((t) => t.name === n);

test("402 from the x402 paywall counts as UP for inference", async () => {
  const r = await probe(T("inference"), fakeFetch({ [url("inference")]: 402 }));
  assert.equal(r.up, true);
});
test("530 tunnel error and timeouts count as DOWN", async () => {
  assert.equal((await probe(T("mcp"), fakeFetch({ [url("mcp")]: 530 }))).up, false);
  const t = await probe(T("mcp"), fakeFetch({ [url("mcp")]: "timeout" }));
  assert.equal(t.up, false); assert.equal(t.error, "timeout");
});
test("first run emails only DOWN targets; later runs only on change", () => {
  const res = [{ name: "a", up: true }, { name: "b", up: false }];
  assert.deepEqual(transitions(null, res).map((r) => r.name), ["b"]);
  assert.deepEqual(transitions({ a: true, b: false }, res), []);
  assert.deepEqual(transitions({ a: false, b: false }, res).map((r) => r.name), ["a"]);
});
test("MIME has no header injection", () => {
  const m = buildMime({ from: "monitor@a11oy.net", to: "x@y.z", subject: "a\r\nBcc: evil@x", text: "hi" });
  assert.ok(!/\r\nBcc:/.test(m));
});
test("run sends a DOWN email once, then nothing while unchanged, then a heartbeat", async () => {
  const env = { STATE: kv() }; const sent = [];
  const sendImpl = async (_e, s) => sent.push(s);
  const f = fakeFetch({ [url("mcp")]: 530 });
  await run(env, { fetchImpl: f, sendImpl });
  await run(env, { fetchImpl: f, sendImpl });
  await run(env, { fetchImpl: f, sendImpl, heartbeat: true });
  assert.equal(sent.length, 2);
  assert.match(sent[0], /mcp DOWN/); assert.match(sent[1], /heartbeat: 1 down/);
});
test("a failed alert send does not save state, so the next run retries the alert", async () => {
  const env = { STATE: kv() }; const sent = []; let fail = true;
  const sendImpl = async (_e, s) => { if (fail) throw new Error("send failed"); sent.push(s); };
  const f = fakeFetch({ [url("mcp")]: 530 });
  await assert.rejects(run(env, { fetchImpl: f, sendImpl }));
  fail = false;
  await run(env, { fetchImpl: f, sendImpl });
  assert.equal(sent.length, 1); assert.match(sent[0], /mcp DOWN/);
});
