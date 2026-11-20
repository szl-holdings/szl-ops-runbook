# Kimi agentic peer coding: bounded source-only intake

Owner: szl-holdings/szl-ops-runbook. Disposition: source-only review, not runtime or production admission.

## Observed local recovery

On BETTERWITHAGE, the local low-precision Kimi-VL-based kimi-estate-ops:latest
alias produced repetitive text that failed the JSON contract. In contrast,
kimi-k3.1-pro:cloud answered through the existing local Ollama endpoint. The
cloud variant may send prompts off-device. Only reviewed public, sanitized
source may enter a cloud prompt; no credentials, private files or account data.

An isolated disposable fixture reproduced a false-ready truthiness bug:
return bool(state) accepted HOLD, UNAVAILABLE and FAILED. Cloud Kimi supplied a
valid one-line correction. The host approved only a reviewed exact replacement,
patched the fixture and reran two regression test methods successfully.
Six further host-boundary test methods passed. This is an unsigned source-only
local coding demonstration, not an admitted release, actual repo repair, or
authenticated runtime recovery.

## Host-controlled peer protocol

1. Host observes exact source repo, 40-hex source head, and allowed path.
2. Kimi proposes JSON matching szl.kimi-peer-proposal/v1. It receives no tool
   grants, local credentials or filesystem authority.
3. Host calls tools.kimi_peer_gate.assess_peer_proposal with independent source
   pin, allowed path set, reviewed replacement lines, and required negative
   controls. Malformed, repetitive, unauthorized or privilege-seeking model
   replies fail closed. The gate never writes or executes model code.
4. Owner separately reviews proposed diff, applies it to an isolated source
   branch, runs independent tests and exact-head CI, and requests normal review.
   A positive intake result is only a SOURCE_ONLY_REVIEW_CANDIDATE.
5. Protected branches, release signatures, authenticated runtime/data rendering,
   HF/Cloudflare/PyPI deployment, DNS, payments and GPU training remain out
   of scope. Nothing grants production admission or a signed receipt.

Reproduce without Ollama, network, secrets or estate credentials:
    python -m pytest tests/test_kimi_peer_gate.py -q

The disposable benchmark and unsigned receipt remain only on BETTERWITHAGE:
    C:\SZL\work\kimi-agentic-recovery-20261119

The gate is not yet integrated with any automatically authorized patcher.
