# Unblocker board — szl-holdings — Wednesday 2026-09-30 21:53 ET

15 open PRs · 0 ready to merge · 0 on HOLD · blockers: PROVENANCE_BODY 15, TESTS_RED 7, DRAFT_GATE 5, HF_PARITY 2, CP_EFFECT 2

## Top fixes before you start coding
- **PROVENANCE_BODY** unblocks 15 PR(s): PR body missing headings: Origin, Rights, Agents and tools, Tests, Security, Rollback, Known limits. → runbook `pr-provenance-headings`  
  a11oy#2318, a11oy#2360, immune#155, platform#601, szl-forge#295, .github#819, .github#820, a11oy#2400, a11oy-factory#52, hatun-mcp#127, holographic-unify#29, szl-atelier#34, szl-khipu#81, szl-real-estate#22, szl-substrate#22
- **TESTS_RED** unblocks 6 PR(s): Open the failing step log. → runbook `red-workflows-scan`  
  platform#601, szl-forge#295, a11oy-factory#52, holographic-unify#29, szl-real-estate#22, szl-substrate#22
- **DRAFT_GATE** unblocks 5 PR(s): Draft PRs fail the exact-head provenance gate by design; mark ready when it should merge. → runbook `pr-exact-head-provenance`  
  a11oy#2318, a11oy#2360, immune#155, platform#601, szl-forge#295
- **HF_PARITY** unblocks 2 PR(s): Update the branch to the live main head. → runbook `a11oy-parity-single-writer`  
  a11oy#2318, a11oy#2360
- **CP_EFFECT** unblocks 2 PR(s): Split or pin the effectful workflow change; extend the effect policy only with a receipt. → runbook `pr-control-plane-effect`  
  .github#819, .github#820
- **TESTS_RED** unblocks 1 PR(s): Squash to one conventional commit when merging; rebase if the branch is stale. → runbook `pr-conflicting`  
  platform#601

## Every open PR, ranked by the cheapest unblock

| PR | state | blocker → fix | runbook | stale |
|---|---|---|---|---|
| [a11oy#2318](https://github.com/szl-holdings/a11oy/pull/2318) feat(brand): adopt SZL Kanchay design system — docs site | DRAFT MERGEABLE/UNSTABLE | HF_PARITY (Protected base matches immutable HF repository); DRAFT_GATE; PROVENANCE_BODY | `a11oy-parity-single-writer`, `pr-exact-head-provenance`, `pr-provenance-headings` | 0d |
| [a11oy#2360](https://github.com/szl-holdings/a11oy/pull/2360) fix(ui): keep console reads passive and mobile evidence accessible | DRAFT MERGEABLE/UNSTABLE | HF_PARITY (Protected base matches immutable HF repository); DRAFT_GATE; PROVENANCE_BODY | `a11oy-parity-single-writer`, `pr-exact-head-provenance`, `pr-provenance-headings` | 0d |
| [immune#155](https://github.com/szl-holdings/immune/pull/155) fix(immune): qualify external v2 authority and durable readiness | DRAFT MERGEABLE/CLEAN | DRAFT_GATE; PROVENANCE_BODY | `pr-exact-head-provenance`, `pr-provenance-headings` | 0d |
| [platform#601](https://github.com/szl-holdings/platform/pull/601) feat(a11oy): complete P0 product journey and exact-source proof | DRAFT UNKNOWN/UNKNOWN | TESTS_RED (Lint commit messages); TESTS_RED (truth-drift); DRAFT_GATE; PROVENANCE_BODY | `pr-conflicting`, `pr-exact-head-provenance`, `pr-provenance-headings`, `red-workflows-scan` | 0d |
| [szl-forge#295](https://github.com/szl-holdings/szl-forge/pull/295) feat(frontier): execute isolated vLLM-Omni runtime prerequisite observ | DRAFT UNKNOWN/UNKNOWN | TESTS_RED (observe (3.11)); DRAFT_GATE; PROVENANCE_BODY | `pr-exact-head-provenance`, `pr-provenance-headings`, `red-workflows-scan` | 0d |
| [.github#819](https://github.com/szl-holdings/.github/pull/819) fix(ci): FORGE-9 attests only PR/merge-group runs | MERGEABLE/BLOCKED | CP_EFFECT (Static control-plane effect boundary); PROVENANCE_BODY (szl/provenance) | `pr-control-plane-effect`, `pr-provenance-headings` | 0d |
| [.github#820](https://github.com/szl-holdings/.github/pull/820) ci: mirror canonical GHCR images to Docker Hub (digest-verified, recei | MERGEABLE/BLOCKED | CP_EFFECT (Static control-plane effect boundary); PROVENANCE_BODY (szl/provenance) | `pr-control-plane-effect`, `pr-provenance-headings` | 0d |
| [a11oy#2400](https://github.com/szl-holdings/a11oy/pull/2400) feat(brainsentry): cve + cvss v3.1 enrichment for defensive triage | MERGEABLE/BLOCKED | PROVENANCE_BODY | `pr-provenance-headings` | 0d |
| [a11oy-factory#52](https://github.com/szl-holdings/a11oy-factory/pull/52) chore(deps): bump brace-expansion | MERGEABLE/UNSTABLE | TESTS_RED (quality); PROVENANCE_BODY | `pr-provenance-headings`, `red-workflows-scan` | 0d |
| [hatun-mcp#127](https://github.com/szl-holdings/hatun-mcp/pull/127) feat: MCP Registry listing (server.json + OIDC publish workflow + rece | MERGEABLE/BLOCKED | PROVENANCE_BODY | `pr-provenance-headings` | 0d |
| [holographic-unify#29](https://github.com/szl-holdings/holographic-unify/pull/29) feat(frontend): join SZL Holographic Space Fabric v2 | UNKNOWN/UNKNOWN | TESTS_RED (runtime-contract); PROVENANCE_BODY | `pr-provenance-headings`, `red-workflows-scan` | 0d |
| [szl-atelier#34](https://github.com/szl-holdings/szl-atelier/pull/34) feat(frontend): join SZL Holographic Space Fabric v2 | MERGEABLE/CLEAN | PROVENANCE_BODY | `pr-provenance-headings` | 0d |
| [szl-khipu#81](https://github.com/szl-holdings/szl-khipu/pull/81) feat(frontend): join SZL Holographic Space Fabric v2 | MERGEABLE/CLEAN | PROVENANCE_BODY | `pr-provenance-headings` | 0d |
| [szl-real-estate#22](https://github.com/szl-holdings/szl-real-estate/pull/22) ci: OpenSSF Scorecard (org reusable, SHA-pinned caller) — Wave H | MERGEABLE/UNSTABLE | TESTS_RED (Verify canonical Terra surface owner); PROVENANCE_BODY | `pr-provenance-headings`, `red-workflows-scan` | 0d |
| [szl-substrate#22](https://github.com/szl-holdings/szl-substrate/pull/22) ci: OpenSSF Scorecard (org reusable, SHA-pinned caller) — Wave H | MERGEABLE/UNSTABLE | TESTS_RED (Lint PR title (Conventional Commits)); PROVENANCE_BODY | `pr-provenance-headings`, `red-workflows-scan` | 0d |

## Red on main (latest run per workflow)
- .github · Publish Nexus Space · failure · [2026-10-01](https://github.com/szl-holdings/.github/actions/runs/36803134581)
- .github · FORGE-9 attest and approve · failure · [2026-10-01](https://github.com/szl-holdings/.github/actions/runs/36803123962)
- a11oy · Investor smoke gate (S1–S12) · failure · [2026-10-01](https://github.com/szl-holdings/a11oy/actions/runs/36801123811)
- a11oy-factory · Dependabot Updates · failure · [2026-10-01](https://github.com/szl-holdings/a11oy-factory/actions/runs/36802953552)
- immune · Dependabot Updates · failure · [2026-09-29](https://github.com/szl-holdings/immune/actions/runs/36593063001)

_Read-only snapshot. Nothing was merged, edited, or re-run by this board._
