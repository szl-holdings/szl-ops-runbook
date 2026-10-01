# Unblocker board — szl-holdings — Wednesday 2026-09-30 22:04 ET

7 open PRs · 1 ready to merge · 0 on HOLD · blockers: DRAFT_GATE 5, TESTS_RED 4, HF_PARITY 2, READY 1, BEHIND 1

## Top fixes before you start coding
- **DRAFT_GATE** unblocks 5 PR(s): Draft PRs fail the exact-head provenance gate by design; mark ready when it should merge. → runbook `pr-exact-head-provenance`  
  platform#601, a11oy#2318, a11oy#2360, immune#155, szl-forge#295
- **TESTS_RED** unblocks 3 PR(s): Open the failing step log. → runbook `red-workflows-scan`  
  platform#601, szl-forge#295, holographic-unify#29
- **HF_PARITY** unblocks 2 PR(s): Update the branch to the live main head. → runbook `a11oy-parity-single-writer`  
  a11oy#2318, a11oy#2360
- **BEHIND** unblocks 1 PR(s): gh pr update-branch --rebase, then re-check provenance. → runbook `pr-behind-main`  
  platform#601
- **TESTS_RED** unblocks 1 PR(s): Squash to one conventional commit when merging; rebase if the branch is stale. → runbook `pr-conflicting`  
  platform#601

## Ready to merge (squash)
- [a11oy-factory#52](https://github.com/szl-holdings/a11oy-factory/pull/52) chore(deps): bump brace-expansion · +10/-65 · 1 files

## Every open PR, ranked by the cheapest unblock

| PR | state | blocker → fix | runbook | stale |
|---|---|---|---|---|
| [a11oy-factory#52](https://github.com/szl-holdings/a11oy-factory/pull/52) chore(deps): bump brace-expansion | MERGEABLE/CLEAN | READY | `pr-merge-conveyor` | 0d |
| [platform#601](https://github.com/szl-holdings/platform/pull/601) feat(a11oy): complete P0 product journey and exact-source proof | DRAFT MERGEABLE/BEHIND | BEHIND; TESTS_RED (Lint commit messages); TESTS_RED (truth-drift); DRAFT_GATE | `pr-behind-main`, `pr-conflicting`, `pr-exact-head-provenance`, `red-workflows-scan` | 0d |
| [a11oy#2318](https://github.com/szl-holdings/a11oy/pull/2318) feat(brand): adopt SZL Kanchay design system — docs site | DRAFT UNKNOWN/UNKNOWN | HF_PARITY (Protected base matches immutable HF repository); DRAFT_GATE | `a11oy-parity-single-writer`, `pr-exact-head-provenance` | 0d |
| [a11oy#2360](https://github.com/szl-holdings/a11oy/pull/2360) fix(ui): keep console reads passive and mobile evidence accessible | DRAFT UNKNOWN/UNKNOWN | HF_PARITY (Protected base matches immutable HF repository); DRAFT_GATE | `a11oy-parity-single-writer`, `pr-exact-head-provenance` | 0d |
| [immune#155](https://github.com/szl-holdings/immune/pull/155) fix(immune): qualify external v2 authority and durable readiness | DRAFT MERGEABLE/CLEAN | DRAFT_GATE | `pr-exact-head-provenance` | 0d |
| [szl-forge#295](https://github.com/szl-holdings/szl-forge/pull/295) feat(frontier): execute isolated vLLM-Omni runtime prerequisite observ | DRAFT UNKNOWN/UNKNOWN | TESTS_RED (observe (3.11)); DRAFT_GATE | `pr-exact-head-provenance`, `red-workflows-scan` | 0d |
| [holographic-unify#29](https://github.com/szl-holdings/holographic-unify/pull/29) feat(frontend): join SZL Holographic Space Fabric v2 | MERGEABLE/BLOCKED | TESTS_RED (runtime-contract) | `red-workflows-scan` | 0d |

## Red on main (latest run per workflow)
- a11oy-factory · Dependabot Updates · failure · [2026-10-01](https://github.com/szl-holdings/a11oy-factory/actions/runs/36802953552)
- immune · Dependabot Updates · failure · [2026-09-29](https://github.com/szl-holdings/immune/actions/runs/36593063001)

_Read-only snapshot. Nothing was merged, edited, or re-run by this board._
