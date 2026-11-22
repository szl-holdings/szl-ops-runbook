# Alert delivery admission — preserve measured denominators

**Status:** Source-only, untrusted observation classifier. **Deployed monitor:** UNVERIFIED. **Verified subscriber delivery:** UNVERIFIED. This addition never sends email or alerts, calls models, changes infrastructure, or grants release approval.

## Actual accepted SLO and observed blocker

The current 30-day alert SLO in slo/slos.yaml requires a relay publish acknowledgement in **strictly less than five seconds** and a separately correlated subscriber receipt **within sixty seconds**. The availability target is 99.5%; a real measured baseline remains unknown. A11oy alert-relay [PR #3793](https://github.com/szl-holdings/a11oy/pull/3793) specifies a 25-second provider timeout: this can outlast that five-second objective. A shorter timeout would report failure sooner, **not** make the upstream deliver messages.

A historical synthetic delivery attempt returned 429 from ntfy.sh. [Official ntfy rate-limit documentation](https://docs.ntfy.sh/config/) confirms 429 and optional Retry-After signals; a timeout change alone does not address provider quota. Do not automatically retry uncertain sends. The relay's live revision endpoint returning HTTP 200 is not proof of subscriber delivery.

The earlier [PR #3570](https://github.com/szl-holdings/a11oy/pull/3570) was closed without merge; #3793 is its successor and remains separately review-gated. Protect live subscriber secrets and opaque ntfy paths from monitoring logs.

## Implemented offline evaluator

The new alerts/delivery_witness.py consumes only caller-declared, exact-shape samples. It separates 429 RATE_LIMITED_NO_RETRY; 504 UNKNOWN_DELIVERY_NO_RETRY; 502/5xx upstream failures; missing or uncorrelated subscriber receipt; five-second ACK breaches; and sixty-second subscriber breaches.

Zero samples remain UNOBSERVED rather than counted as a success. Mixed samples retain the **input-row** denominator and report the number that satisfy **reported** conditions. There is no trusted per-alert identity in the v1 claim, so `claimed_attempts_observed` counts received rows, **not proven unique attempts**. Repeated, byte-equivalent positive evidence is labeled `POSSIBLE_DUPLICATE_CLAIMS_UNVERIFIED` and counted in `possible_duplicate_positive_claim_rows`. This does **not** establish replay or duplication of real deliveries: independent alerts can legitimately share the same reported metrics. Conversely, distinct rows do not prove distinct attempts. No alert identity or payload content is emitted in the summary. Every batch retains `distinct_attempt_identities_verified=false`.

Even a fully coherent caller declaration is REPORTED_CONDITIONS_MET_NOT_VERIFIED: all independent signature, real subscriber verification, production readiness, release and automatic-retry authorizations stay FALSE. Neither the origin nor integrity of a claimed receipt is verified. A new genuinely verified receipt workflow would need independent correlation IDs, a stable trusted time source, signature checks and actual subscriber-side evidence rather than inferring uniqueness from these untrusted rows.

Run from repository root:

    python -m unittest discover -s tests -p test_delivery_witness.py -v

The pure deadline compatibility check reports WORKER_DEADLINE_CAN_OUTLAST_ACK_SLO when given 25000ms. This is a design risk, not proof of actual latency or outage.

## Owner-controlled operating sequence

1. Verify current provider quota and keep any 429, 502, 504 and missing subscriber receipts visible; never synthesize green, auto-ack a failed alert, or auto-retry UNKNOWN.
2. Establish an approved alternate or expanded channel: managed ntfy account/tier, independently operated authenticated ntfy with rate control, or separately approved email delivery. Cloudflare Email Service requires sender-domain onboarding and verified recipient bindings. Do not guess recipient addresses, authorize spending without bounds, or send messages just because a sample had status 200.
3. Independently measure client-to-relay latency (<5s) and correlated receipt at subscriber (<=60s) using a defined observer and trustworthy receipt. Also retain 429, timeout, retry, duplicate and missing-monitor denominators.
4. Determine the exact intended five public URLs and separately approved monitor-recipient address; a local cron job or unreviewed source file is not proof that external email alerts run.
5. Release only after normal protected CI, an independent authorized reviewer, approved deployment window, exact Worker revision readback, provider-delivery canary and subscriber receipt. This work does not change Cloudflare, HF, signed execution, GPU training or Flagship54.

## Model review disposition

The public-prompt Kimi K3.1 Pro review suggested retrying UNKNOWN deliveries; **not accepted**, because an unknown result could already be delivered and the relay forbids blind retries. Mistral Large 4 challenged retries and false positive delivery claims. Its suggested subscriber-signature proof remains future research, not currently verified. AI model agreement is never operator authorization.

## Separate signed A11oy execution gate

A11oy's first live signed five-case test on a new boot requires distinct P-256 approval and runtime signer authorities, authenticated admin/operator bindings, a reviewed bounded plan, exact immutable source/HF/boot identity and current fenced storage. The source-only tool provides none of these. The user has not named an independent approval custodian, code-admin key holder or approved monitor email recipient; none were invented. No paid model calls were made.
