# Unblocker board — szl-holdings — Friday 2026-10-02 07:32 ET

48 open PRs · 8 ready to merge · 1 on HOLD · blockers: BEHIND 17, DRAFT_GATE 15, CONFLICTING 9, READY 8, SECURITY_GATE 3, TESTS_RED 3, CP_EFFECT 2, PROVENANCE_BODY 2, HF_PARITY 1, HOLD 1, FRONT_DOOR 1

## Top fixes before you start coding
- **BEHIND** unblocks 17 PR(s): gh pr update-branch --rebase, then re-check provenance. → runbook `pr-behind-main`  
  a11oy#2411, a11oy#2414, a11oy#2415, a11oy#2416, a11oy#2422, a11oy#2427, a11oy#2435, a11oy#2436, a11oy#2441, szl-estate-os#63, szl-forge#484, szl-forge#491, szl-forge#500, szl-frontier#214, szl-kernels#47, szl-typesafe-triage#44, szl-typesafe-triage#50
- **DRAFT_GATE** unblocks 15 PR(s): Draft PRs fail the exact-head provenance gate by design; mark ready when it should merge. → runbook `pr-exact-head-provenance`  
  szl-estate-os#63, .github#831, .github#833, david-leads#139, governed-receipt-spec#31, immune#159, platform#876, platform#877, platform#878, szl-org-health#218, szl-skills#19, szl-skills#21, szl-skills#30, szl-skills#35, szl-skills#36
- **CONFLICTING** unblocks 9 PR(s): Rebase onto main and resolve, or close as net-zero with a receipt comment. → runbook `pr-conflicting`  
  szl-org-health#218, szl-skills#19, szl-skills#21, szl-skills#35, a11oy#2413, a11oy#2429, szl-skills#22, szl-skills#28, szl-skills#32
- **SECURITY_GATE** unblocks 3 PR(s): Clear HIGH CVEs with root pnpm overrides. → runbook `security-gate-platform`  
  platform#876, platform#877, platform#878
- **TESTS_RED** unblocks 3 PR(s): Open the failing step log. → runbook `red-workflows-scan`  
  szl-org-health#218, szl-skills#19, a11oy#2429
- **PROVENANCE_BODY** unblocks 2 PR(s): Add the seven policy headings to the PR body (template in templates/pr-body.md). → runbook `pr-provenance-headings`  
  .github#833, .github#830

## Ready to merge (squash)
- [immune#157](https://github.com/szl-holdings/immune/pull/157) fix(immune): distinguish empty and corrupt receipt ledgers · +69/-10 · 4 files
- [immune#158](https://github.com/szl-holdings/immune/pull/158) fix(immune): preserve corrupt state and distinguish empty ledgers · +120/-8 · 4 files
- [szl-evidence-mandate#6](https://github.com/szl-holdings/szl-evidence-mandate/pull/6) Make signed evidence receipts schema-conformant and enforceable · +107/-8 · 8 files
- [szl-lambda-gate#64](https://github.com/szl-holdings/szl-lambda-gate/pull/64) fix(hf): check named Hub tag without listing gated refs · +59/-5 · 2 files
- [szl-skills#27](https://github.com/szl-holdings/szl-skills/pull/27) fix(science): fail closed on ambiguous skill identities · +156/-17 · 4 files
- [szl-skills#33](https://github.com/szl-holdings/szl-skills/pull/33) feat(science): pilot exact range propagation · +618/-0 · 8 files
- [szl-skills#34](https://github.com/szl-holdings/szl-skills/pull/34) test(science): pilot offline package-to-result continuity · +592/-0 · 4 files
- [szl-typesafe-triage#52](https://github.com/szl-holdings/szl-typesafe-triage/pull/52) fix(triage): publish canonical cards with immutable readback · +1000/-63 · 4 files

## Every open PR, ranked by the cheapest unblock

| PR | state | blocker → fix | runbook | stale |
|---|---|---|---|---|
| [immune#157](https://github.com/szl-holdings/immune/pull/157) fix(immune): distinguish empty and corrupt receipt ledgers | MERGEABLE/CLEAN | READY | `pr-merge-conveyor` | 0d |
| [immune#158](https://github.com/szl-holdings/immune/pull/158) fix(immune): preserve corrupt state and distinguish empty ledgers | MERGEABLE/CLEAN | READY | `pr-merge-conveyor` | 0d |
| [szl-evidence-mandate#6](https://github.com/szl-holdings/szl-evidence-mandate/pull/6) Make signed evidence receipts schema-conformant and enforceable | MERGEABLE/CLEAN | READY | `pr-merge-conveyor` | 0d |
| [szl-lambda-gate#64](https://github.com/szl-holdings/szl-lambda-gate/pull/64) fix(hf): check named Hub tag without listing gated refs | MERGEABLE/CLEAN | READY | `pr-merge-conveyor` | 0d |
| [szl-skills#27](https://github.com/szl-holdings/szl-skills/pull/27) fix(science): fail closed on ambiguous skill identities | MERGEABLE/CLEAN | READY | `pr-merge-conveyor` | 0d |
| [szl-skills#33](https://github.com/szl-holdings/szl-skills/pull/33) feat(science): pilot exact range propagation | MERGEABLE/CLEAN | READY | `pr-merge-conveyor` | 0d |
| [szl-skills#34](https://github.com/szl-holdings/szl-skills/pull/34) test(science): pilot offline package-to-result continuity | MERGEABLE/CLEAN | READY | `pr-merge-conveyor` | 0d |
| [szl-typesafe-triage#52](https://github.com/szl-holdings/szl-typesafe-triage/pull/52) fix(triage): publish canonical cards with immutable readback | MERGEABLE/CLEAN | READY | `pr-merge-conveyor` | 0d |
| [a11oy#2411](https://github.com/szl-holdings/a11oy/pull/2411) fix(payloads/lambda_gate): zeroed axis yields exactly 0.0 — the Λ veto | MERGEABLE/BEHIND | BEHIND | `pr-behind-main` | 0d |
| [a11oy#2414](https://github.com/szl-holdings/a11oy/pull/2414) chore(amaru/receipts): canonical JSON via szl-evidence-core — profile  | MERGEABLE/BEHIND | BEHIND | `pr-behind-main` | 0d |
| [a11oy#2415](https://github.com/szl-holdings/a11oy/pull/2415) fix(inventory): include reserved public organization Space | MERGEABLE/BEHIND | BEHIND | `pr-behind-main` | 0d |
| [a11oy#2416](https://github.com/szl-holdings/a11oy/pull/2416) fix(finance): expose bounded upstream response rejection evidence | MERGEABLE/BEHIND | BEHIND | `pr-behind-main` | 0d |
| [a11oy#2422](https://github.com/szl-holdings/a11oy/pull/2422) fix(finance): expose source-bound version endpoint | MERGEABLE/BEHIND | BEHIND | `pr-behind-main` | 0d |
| [a11oy#2427](https://github.com/szl-holdings/a11oy/pull/2427) feat(brand): adopt SZL KANCHAY founder direction in docs | MERGEABLE/BEHIND | BEHIND | `pr-behind-main` | 0d |
| [a11oy#2435](https://github.com/szl-holdings/a11oy/pull/2435) fix(ci): validate router source authority without writes | MERGEABLE/BEHIND | BEHIND; HF_PARITY (Protected base matches immutable HF repository) | `a11oy-parity-single-writer`, `pr-behind-main` | 0d |
| [a11oy#2436](https://github.com/szl-holdings/a11oy/pull/2436) fix(runtime): persist sovereign receipts and relock HF assets | MERGEABLE/BEHIND | BEHIND | `pr-behind-main` | 0d |
| [a11oy#2441](https://github.com/szl-holdings/a11oy/pull/2441) fix(finance): use dated ECB reference FX when Frankfurter fails | MERGEABLE/BEHIND | BEHIND | `pr-behind-main` | 0d |
| [szl-estate-os#63](https://github.com/szl-holdings/szl-estate-os/pull/63) docs(estate): record source closure and operational holds | DRAFT MERGEABLE/BEHIND | BEHIND; DRAFT_GATE | `pr-behind-main`, `pr-exact-head-provenance` | 0d |
| [szl-forge#484](https://github.com/szl-holdings/szl-forge/pull/484) tools(estate_payload): reconcile managed candidates and fix Windows co | MERGEABLE/BEHIND | BEHIND | `pr-behind-main` | 0d |
| [szl-forge#491](https://github.com/szl-holdings/szl-forge/pull/491) fix(frontier): frame model events on LF only | MERGEABLE/BEHIND | BEHIND | `pr-behind-main` | 0d |
| [szl-forge#500](https://github.com/szl-holdings/szl-forge/pull/500) fix(clinical): verify wheel bytes against immutable source before inst | MERGEABLE/BEHIND | BEHIND | `pr-behind-main` | 0d |
| [szl-frontier#214](https://github.com/szl-holdings/szl-frontier/pull/214) fix(lambda_gate): refusals carry szl.lambda/v1 codes; bool is not a nu | MERGEABLE/BEHIND | BEHIND | `pr-behind-main` | 0d |
| [szl-kernels#47](https://github.com/szl-holdings/szl-kernels/pull/47) ci: drift guard — UnifiedReceiptChain byte-identical to szl-evidence-c | MERGEABLE/BEHIND | BEHIND | `pr-behind-main` | 0d |
| [szl-typesafe-triage#44](https://github.com/szl-holdings/szl-typesafe-triage/pull/44) [HOLD: twelfth gate] release v1.1.0 — refusal-retrained five-seed stud | MERGEABLE/BEHIND | HOLD; BEHIND | `pr-behind-main` | 0d |
| [szl-typesafe-triage#50](https://github.com/szl-holdings/szl-typesafe-triage/pull/50) test(lambda): re-vendor szl.lambda/v1 golden vectors 50 → 60 (zero nev | MERGEABLE/BEHIND | BEHIND | `pr-behind-main` | 0d |
| [.github#831](https://github.com/szl-holdings/.github/pull/831) fix(estate): admit exact operational inventory effects | DRAFT UNKNOWN/UNKNOWN | DRAFT_GATE | `pr-exact-head-provenance` | 0d |
| [.github#833](https://github.com/szl-holdings/.github/pull/833) fix: align v5 livez probe with process-only contract | DRAFT UNKNOWN/UNKNOWN | DRAFT_GATE; CP_EFFECT (Static control-plane effect boundary); PROVENANCE_BODY (szl/provenance) | `pr-control-plane-effect`, `pr-exact-head-provenance`, `pr-provenance-headings` | 0d |
| [david-leads#139](https://github.com/szl-holdings/david-leads/pull/139) Require live federal lane proof for Space deployment success | DRAFT MERGEABLE/CLEAN | DRAFT_GATE | `pr-exact-head-provenance` | 0d |
| [governed-receipt-spec#31](https://github.com/szl-holdings/governed-receipt-spec/pull/31) fix: fail closed on ambiguous receipt JSON and malformed evidence | DRAFT MERGEABLE/CLEAN | DRAFT_GATE | `pr-exact-head-provenance` | 0d |
| [immune#159](https://github.com/szl-holdings/immune/pull/159) fix(immune): preserve hash-corrupt persisted ledgers | DRAFT MERGEABLE/CLEAN | DRAFT_GATE | `pr-exact-head-provenance` | 0d |
| [platform#876](https://github.com/szl-holdings/platform/pull/876) fix(estate): fail closed on partial source and CI evidence | DRAFT MERGEABLE/BLOCKED | SECURITY_GATE (Dependency Vulnerability Scan); DRAFT_GATE | `pr-exact-head-provenance`, `security-gate-platform` | 0d |
| [platform#877](https://github.com/szl-holdings/platform/pull/877) feat(agents-sdk-bridge): add source-only SZL Evidence Steward | DRAFT MERGEABLE/BLOCKED | SECURITY_GATE (Dependency Vulnerability Scan); DRAFT_GATE | `pr-exact-head-provenance`, `security-gate-platform` | 0d |
| [platform#878](https://github.com/szl-holdings/platform/pull/878) fix(readiness-operability): preserve pinned source evidence states | DRAFT MERGEABLE/BLOCKED | SECURITY_GATE (Dependency Vulnerability Scan); DRAFT_GATE | `pr-exact-head-provenance`, `security-gate-platform` | 0d |
| [szl-org-health#218](https://github.com/szl-holdings/szl-org-health/pull/218) Harden PyPI release-path audit evidence checks | DRAFT CONFLICTING/DIRTY | CONFLICTING; TESTS_RED (audit / fail-closed); DRAFT_GATE | `pr-conflicting`, `pr-exact-head-provenance`, `red-workflows-scan` | 0d |
| [szl-skills#19](https://github.com/szl-holdings/szl-skills/pull/19) feat(science): preserve withdrawn dependencies in research recheck pla | DRAFT CONFLICTING/DIRTY | CONFLICTING; TESTS_RED (selfcheck); DRAFT_GATE | `pr-conflicting`, `pr-exact-head-provenance`, `red-workflows-scan` | 0d |
| [szl-skills#21](https://github.com/szl-holdings/szl-skills/pull/21) feat(science): add offline skill package update review | DRAFT CONFLICTING/DIRTY | CONFLICTING; DRAFT_GATE | `pr-conflicting`, `pr-exact-head-provenance` | 0d |
| [szl-skills#30](https://github.com/szl-holdings/szl-skills/pull/30) feat(science): add bounded public OSF registration witness pilot | DRAFT MERGEABLE/CLEAN | DRAFT_GATE | `pr-exact-head-provenance` | 0d |
| [szl-skills#35](https://github.com/szl-holdings/szl-skills/pull/35) feat(science): preserve retired dependencies in change-impact reviews | DRAFT CONFLICTING/DIRTY | CONFLICTING; DRAFT_GATE | `pr-conflicting`, `pr-exact-head-provenance` | 0d |
| [szl-skills#36](https://github.com/szl-holdings/szl-skills/pull/36) fix(science): retain replay refusal receipts and isolate CLI engine | DRAFT MERGEABLE/CLEAN | DRAFT_GATE | `pr-exact-head-provenance` | 0d |
| [.github#830](https://github.com/szl-holdings/.github/pull/830) docs: make SZL front-door cards clearer on mobile | UNKNOWN/UNKNOWN | FRONT_DOOR (Exact taxonomy, front doors, and publication set); PROVENANCE_BODY (szl/provenance) | `org-profile-validators`, `pr-provenance-headings` | 0d |
| [a11oy#2413](https://github.com/szl-holdings/a11oy/pull/2413) feat: add read-only civilian observatory | CONFLICTING/DIRTY | CONFLICTING | `pr-conflicting` | 0d |
| [a11oy#2429](https://github.com/szl-holdings/a11oy/pull/2429) fix(release): make Lyte publication a guarded transaction | CONFLICTING/DIRTY | CONFLICTING; TESTS_RED (Finance source contract (3.12)) | `pr-conflicting`, `red-workflows-scan` | 0d |
| [szl-skills#22](https://github.com/szl-holdings/szl-skills/pull/22) feat(science): audit complete hypothesis families before significance  | CONFLICTING/DIRTY | CONFLICTING | `pr-conflicting` | 0d |
| [szl-skills#28](https://github.com/szl-holdings/szl-skills/pull/28) feat(science): preserve outcomes and stage the complete skill pack | CONFLICTING/DIRTY | CONFLICTING | `pr-conflicting` | 0d |
| [szl-skills#32](https://github.com/szl-holdings/szl-skills/pull/32) Add bounded measurement harmonizer to split science pack | CONFLICTING/DIRTY | CONFLICTING | `pr-conflicting` | 0d |
| [.github#832](https://github.com/szl-holdings/.github/pull/832) fix(hf): bound native kernel discovery and withhold private inventory | UNKNOWN/UNKNOWN | CP_EFFECT (Static control-plane effect boundary) | `pr-control-plane-effect` | 0d |
| [szl-receipt#46](https://github.com/szl-holdings/szl-receipt/pull/46) test(lambda): re-vendor szl.lambda/v1 golden vectors 50 → 60 (zero nev | MERGEABLE/BLOCKED | — | — | 0d |
| [uds-bundles#70](https://github.com/szl-holdings/uds-bundles/pull/70) fix(test): use one unittest import style | MERGEABLE/BLOCKED | — | — | 0d |

## Red on main (latest run per workflow)
- .github · HF Living Constellation Operator · failure · [2026-10-02](https://github.com/szl-holdings/.github/actions/runs/37001505107)
- .github · Publish Nexus Space · failure · [2026-10-02](https://github.com/szl-holdings/.github/actions/runs/37001419285)
- .github · estate-governance-scorecard · failure · [2026-10-02](https://github.com/szl-holdings/.github/actions/runs/37001037391)
- .github · Estate dead-man supervisor · failure · [2026-10-02](https://github.com/szl-holdings/.github/actions/runs/37000573298)
- .github · FORGE-9 attest and approve · failure · [2026-10-02](https://github.com/szl-holdings/.github/actions/runs/36999568414)
- a11oy · Brain Frontier v7 refresh · failure · [2026-10-02](https://github.com/szl-holdings/a11oy/actions/runs/36995152318)
- david-leads · David frontier live-lanes canary · failure · [2026-10-02](https://github.com/szl-holdings/david-leads/actions/runs/36975315617)
- david-leads · Rotate David Space credentials · failure · [2026-09-30](https://github.com/szl-holdings/david-leads/actions/runs/36788140207)
- governed-receipt-spec · Scorecard · startup_failure · [2026-10-01](https://github.com/szl-holdings/governed-receipt-spec/actions/runs/36803011306)
- immune · Deploy IMMUNE Spaces · failure · [2026-10-01](https://github.com/szl-holdings/immune/actions/runs/36917371243)
- platform · READINESS-SECURITY · failure · [2026-10-02](https://github.com/szl-holdings/platform/actions/runs/37001273347)
- platform · READINESS-RELIABILITY · failure · [2026-10-02](https://github.com/szl-holdings/platform/actions/runs/36999740769)
- platform · READINESS-OBSERVABILITY · failure · [2026-10-02](https://github.com/szl-holdings/platform/actions/runs/36997240612)
- szl-estate-os · Estate readiness evidence · failure · [2026-10-02](https://github.com/szl-holdings/szl-estate-os/actions/runs/36995711134)
- szl-frontier · Hugging Face frontier watch · failure · [2026-10-01](https://github.com/szl-holdings/szl-frontier/actions/runs/36863742165)
- szl-lambda-gate · hf-mirror · failure · [2026-10-02](https://github.com/szl-holdings/szl-lambda-gate/actions/runs/36965793867)
- szl-typesafe-triage · publish-hf-card · failure · [2026-10-01](https://github.com/szl-holdings/szl-typesafe-triage/actions/runs/36939076612)

## Open issues — 188 (ledger, not noise)
- by repo: szl-forge 49, szl-frontier 37, a11oy 26, .github 21, szl-org-health 12, szl-gpu-bridge 7, killinchu 4, szl-serve 3, vertical-services 2, szl-engine-bench 2, szl-estate-os 2, szl-kernels 2
- by class: frontier-eval 79, other 46, hf-drift 27, estate 16, security 8, owner-queue 6, ci 5, incident 1
- by label: estate:blocked-external 66, estate:p0 50, estate:runtime-drift 26, estate:roadmap 9, estate:code-actionable 8, enhancement 4, incident 4, governance 3
- `estate:p0`: 50 · `estate:code-actionable`: 8

Code-actionable now:
- [szl-forge#211](https://github.com/szl-holdings/szl-forge/issues/211) [EVAL] HF core-stack 5.17/1.15/1.13 compatibility matrix
- [.github#649](https://github.com/szl-holdings/.github/issues/649) [PROTECTION] Require exact-head gates on core main branches
- [szl-wave1-report#1](https://github.com/szl-holdings/szl-wave1-report/issues/1) Verify v0.1.0 — CI green on 9338aaee + first real four-chain consolidation
- [szl-quant-bench#1](https://github.com/szl-holdings/szl-quant-bench/issues/1) Verify v0.1.0 — CI green on a4df504d + first real-model curve
- [szl-engine-bench#1](https://github.com/szl-holdings/szl-engine-bench/issues/1) Verify v0.1.0 — CI green on 73b996a8 + first real-engine measurement
- [szl-retrieval-bench#1](https://github.com/szl-holdings/szl-retrieval-bench/issues/1) Verify v0.1.0 — CI green on f3f9fd6f + first real-corpus run
- [.github#606](https://github.com/szl-holdings/.github/issues/606) Public Experience Frontier v4 rollout: all public surfaces
- [.github#575](https://github.com/szl-holdings/.github/issues/575) SZL Responsive Estate v3 rollout

## Security posture (org)
- Dependabot alerts open: 1 · severity {'low': 1}
- Secret-scanning alerts open: 0
- Managed security configuration 252588 (secret scanning, push protection, Dependabot alerts + security updates, private vuln reporting) is enforced on every repository; code-scanning backlog is tracked in runbook `codeql-scorecard-backlog`.

_Read-only snapshot. Nothing was merged, edited, or re-run by this board._
