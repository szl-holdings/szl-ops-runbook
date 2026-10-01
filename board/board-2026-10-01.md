# Unblocker board — szl-holdings — Wednesday 2026-09-30 21:33 ET

17 open PRs · 1 ready to merge · 4 on HOLD · blockers: PROVENANCE_BODY 13, DRAFT_GATE 13, TESTS_RED 4, HOLD 4, CP_EFFECT 4, BEHIND 3, HF_PARITY 3, SECURITY_GATE 2, READY 1

## Top fixes before you start coding
- **DRAFT_GATE** unblocks 13 PR(s): Draft PRs fail the exact-head provenance gate by design; mark ready when it should merge. → runbook `pr-exact-head-provenance`  
  szl-forge#295, .github#773, .github#774, .github#800, .github#803, .github#810, .github#811, .github#814, a11oy#2318, a11oy#2360, immune#155, platform#601, platform#863
- **PROVENANCE_BODY** unblocks 13 PR(s): PR body missing headings: Origin, Rights, Agents and tools, Tests, Security, Rollback, Known limits. → runbook `pr-provenance-headings`  
  a11oy#2400, szl-forge#295, szl-forge#457, .github#773, .github#774, .github#800, .github#814, a11oy#2318, a11oy#2360, immune#155, platform#601, platform#863, .github#785
- **CP_EFFECT** unblocks 4 PR(s): Split or pin the effectful workflow change; extend the effect policy only with a receipt. → runbook `pr-control-plane-effect`  
  .github#810, .github#811, .github#814, .github#785
- **BEHIND** unblocks 3 PR(s): gh pr update-branch --rebase, then re-check provenance. → runbook `pr-behind-main`  
  a11oy#2400, szl-forge#295, szl-forge#457
- **HF_PARITY** unblocks 3 PR(s): Re-copy shared modules from the owner and update the branch. → runbook `a11oy-parity-single-writer`  
  a11oy#2400, a11oy#2318, a11oy#2360
- **TESTS_RED** unblocks 3 PR(s): Open the failing step log. → runbook `red-workflows-scan`  
  a11oy#2400, szl-forge#295, platform#601

## Ready to merge (squash)
- [.github#818](https://github.com/szl-holdings/.github/pull/818) docs(profile): restore portfolio topology, inference flagship, and HISTORICAL snapshot (one-fabric + router contracts) · +16/-10 · 1 files

## Every open PR, ranked by the cheapest unblock

| PR | state | blocker → fix | runbook | stale |
|---|---|---|---|---|
| [.github#818](https://github.com/szl-holdings/.github/pull/818) docs(profile): restore portfolio topology, inference flagship, and HIS | MERGEABLE/UNSTABLE | READY | `pr-merge-conveyor` | 0d |
| [a11oy#2400](https://github.com/szl-holdings/a11oy/pull/2400) feat(brainsentry): cve + cvss v3.1 enrichment for defensive triage | MERGEABLE/BEHIND | BEHIND; TESTS_RED (Lint PR title (Conventional Commits)); HF_PARITY (Shared source files in sync with killinchu); PROVENANCE_BODY | `a11oy-parity-single-writer`, `pr-behind-main`, `pr-provenance-headings`, `red-workflows-scan` | 0d |
| [szl-forge#295](https://github.com/szl-holdings/szl-forge/pull/295) feat(frontier): execute isolated vLLM-Omni runtime prerequisite observ | DRAFT MERGEABLE/BEHIND | BEHIND; TESTS_RED (observe (3.11)); DRAFT_GATE; PROVENANCE_BODY | `pr-behind-main`, `pr-exact-head-provenance`, `pr-provenance-headings`, `red-workflows-scan` | 0d |
| [szl-forge#457](https://github.com/szl-holdings/szl-forge/pull/457) fix(foundation-confirmation): bind release.zip LFS oid to the frozen d | MERGEABLE/BEHIND | BEHIND; PROVENANCE_BODY | `pr-behind-main`, `pr-provenance-headings` | 0d |
| [.github#773](https://github.com/szl-holdings/.github/pull/773) docs(frontier): Codex estate upgrade brief + operator [HOLD] | DRAFT MERGEABLE/BLOCKED | HOLD; DRAFT_GATE; PROVENANCE_BODY (szl/provenance) | `pr-exact-head-provenance`, `pr-provenance-headings` | 3d |
| [.github#774](https://github.com/szl-holdings/.github/pull/774) docs(hf): 2026-09-25 GitHub ↔ Hugging Face alignment recapture [HOLD] | DRAFT MERGEABLE/BLOCKED | HOLD; DRAFT_GATE; PROVENANCE_BODY (szl/provenance) | `pr-exact-head-provenance`, `pr-provenance-headings` | 3d |
| [.github#800](https://github.com/szl-holdings/.github/pull/800) feat(brand): adopt SZL KANCHAY (founder direction) — org profile and c | DRAFT MERGEABLE/BLOCKED | DRAFT_GATE; PROVENANCE_BODY (szl/provenance) | `pr-exact-head-provenance`, `pr-provenance-headings` | 0d |
| [.github#803](https://github.com/szl-holdings/.github/pull/803) HOLD: feat(brand): founder palette for the Holographic Space fabric | DRAFT MERGEABLE/BLOCKED | HOLD; DRAFT_GATE | `pr-exact-head-provenance` | 0d |
| [.github#810](https://github.com/szl-holdings/.github/pull/810) fix(governance): require effective main merge-queue evidence | DRAFT MERGEABLE/UNSTABLE | DRAFT_GATE; CP_EFFECT (Static control-plane effect boundary) | `pr-control-plane-effect`, `pr-exact-head-provenance` | 0d |
| [.github#811](https://github.com/szl-holdings/.github/pull/811) feat(estate): add bounded source inventory and operational receipts | DRAFT MERGEABLE/UNSTABLE | DRAFT_GATE; CP_EFFECT (Static control-plane effect boundary); SECURITY_GATE (trivy) | `pr-control-plane-effect`, `pr-exact-head-provenance`, `security-gate-platform` | 0d |
| [.github#814](https://github.com/szl-holdings/.github/pull/814) fix: report pinned dataset register eligibility contradictions | DRAFT MERGEABLE/BLOCKED | DRAFT_GATE; CP_EFFECT (Static control-plane effect boundary); PROVENANCE_BODY (szl/provenance) | `pr-control-plane-effect`, `pr-exact-head-provenance`, `pr-provenance-headings` | 0d |
| [a11oy#2318](https://github.com/szl-holdings/a11oy/pull/2318) feat(brand): adopt SZL Kanchay design system — docs site | DRAFT MERGEABLE/UNSTABLE | HF_PARITY (Protected base matches immutable HF repository); DRAFT_GATE; PROVENANCE_BODY | `a11oy-parity-single-writer`, `pr-exact-head-provenance`, `pr-provenance-headings` | 0d |
| [a11oy#2360](https://github.com/szl-holdings/a11oy/pull/2360) fix(ui): keep console reads passive and mobile evidence accessible | DRAFT MERGEABLE/UNSTABLE | HF_PARITY (Protected base matches immutable HF repository); DRAFT_GATE; PROVENANCE_BODY | `a11oy-parity-single-writer`, `pr-exact-head-provenance`, `pr-provenance-headings` | 0d |
| [immune#155](https://github.com/szl-holdings/immune/pull/155) fix(immune): qualify external v2 authority and durable readiness | DRAFT MERGEABLE/CLEAN | DRAFT_GATE; PROVENANCE_BODY | `pr-exact-head-provenance`, `pr-provenance-headings` | 0d |
| [platform#601](https://github.com/szl-holdings/platform/pull/601) feat(a11oy): complete P0 product journey and exact-source proof | DRAFT MERGEABLE/BLOCKED | TESTS_RED (Lint commit messages); TESTS_RED (truth-drift); DRAFT_GATE; PROVENANCE_BODY | `pr-conflicting`, `pr-exact-head-provenance`, `pr-provenance-headings`, `red-workflows-scan` | 0d |
| [platform#863](https://github.com/szl-holdings/platform/pull/863) fix(readiness): separate observations from compliance claims | DRAFT MERGEABLE/BLOCKED | DRAFT_GATE; PROVENANCE_BODY | `pr-exact-head-provenance`, `pr-provenance-headings` | 0d |
| [.github#785](https://github.com/szl-holdings/.github/pull/785) lean-numbers: candidate recount at c2de9d76 [HOLD: axiom regex] | MERGEABLE/BLOCKED | HOLD; CP_EFFECT (Static control-plane effect boundary); PROVENANCE_BODY (szl/provenance); SECURITY_GATE (trivy) | `pr-control-plane-effect`, `pr-provenance-headings`, `security-gate-platform` | 3d |

_Read-only snapshot. Nothing was merged, edited, or re-run by this board._
