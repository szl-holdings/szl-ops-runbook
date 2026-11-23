# Local Ollama advisory council (research/PR-review only)

This is a **source-only**, **read-only** three-seat model council. It runs Kimi (proposer), Mistral (critic) and Qwen (optimizer) sequentially against an explicitly public, immutable-SHA-bound source brief. It cannot approve, merge, close PRs, change GitHub permissions, deploy a Hugging Face Space, handle keys, run training, authorize billing or publish to PyPI.

## Local execution on the governed Ubuntu node

The **actual local** Ollama daemon is on `127.0.0.1:11436`. On the referenced workstation, `127.0.0.1:11434` is a proxy to another compute node; the runner intentionally never uses it. The model allowlist pins full local manifest digests and requires local nonzero weight sizes. Identically named remote/cloud aliases are not evidence of vendor identity.

```sh
python3 -B -m unittest -q tests.test_ollama_local_council
python3 -B tools/ollama_local_council.py \
  --public-brief examples/ollama-public-peer-brief.json \
  --receipt .szl-local-receipts/peer-001.json
```

The sample brief is a **dated public example** for PR #17, not an ongoing GitHub freshness proof. For a new review, obtain the exact current GitHub SHA, verify its public status, and create a new local brief with schema `szl.public-peer-brief/v1`, exact keys `repo, head, draft, body_hold, source_change, public_source_confirmed`. Set `public_source_confirmed` to `true` only after an independent visibility check. The runner never queries GitHub for that check.

The three models receive bounded public text and only a bounded digest/summary of the preceding model's untrusted output. They have no tool calls. The runner rejects redirects, ambient proxy use, duplicate JSON keys, non-finite numbers, unpaired Unicode surrogates, model tool calls, malformed response schemas, partial generations and unexpected manifest revisions. Model responses are **not** independent human reviews.

The receipt is a new local `0600` JSON file (no overwrites), records evidence and model hashes, and always sets `merge_authorized=false`, `deployment_authorized=false` and `signed_receipt=false`. A complete advisory council establishes only that three model responses met a local syntactic contract. CI checks, CodeQL, branch rules, real source freshness, runtime health and any source-owner release admission must be verified separately.

**Operational limitations:** CPU latency can be significant; a healthy local Ollama server does not prove local model quality. Claude CLI may be installed but unauthenticated. GPT-6, Astra and Sol labels in Ollama do not establish authenticated OpenAI model identity, and are not enrolled by this local harness. No paid or cloud model is invoked.
