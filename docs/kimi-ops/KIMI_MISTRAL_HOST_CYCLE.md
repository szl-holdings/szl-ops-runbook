<!-- SPDX-License-Identifier: Apache-2.0 -->

# SZL Kimi × Mistral × operator host: source-only paired engineering cycle

**Owner:** szl-holdings/szl-ops-runbook. **State:** bounded local research
and code review, not a new release controller or production inference gateway.

## Existing components, connected rather than duplicated

1. `tools/ollama_peer_consult.py` elicits **independent** Kimi K3.1 Pro
   and Mistral Large 4 opinions through a fixed loopback Ollama endpoint.
   It requires an operator-confirmed *public* excerpt and a 40-character
   GitHub source SHA; no model gets GitHub, filesystem or shell tools.
2. `tools/ollama_peer_crossreview.py` uses that same first-pass adapter
   and sends a JSON-quoted, bounded, checked *other model response* to each
   model for a second, adversarial critique. It refuses partial/tool-call
   responses, non-JSON/duplicate-key votes, unsupported verdicts, and
   potential credential-bearing model text before forwarding it to another
   provider. Raw first-pass model text is not retained in the bridge receipt.
3. The operator independently runs tests against the exact public
   source and proposed patch, verifies GitHub's actual PR/branch policy,
   and may construct a `mesh_advisory_packet` with a patch digest.
   Existing `szl-mesh/src/szl_mesh/peer_code_review.py` then
   recompiles the packet. Until independently verified test evidence is
   attached *outside this module*, its status stays `UNAVAILABLE`,
   and the mesh compiler returns **HOLD/TESTS_UNAVAILABLE** even if both
   model votes say APPROVE.

**Mistral is not a GitHub reviewer or release authority. Kimi is not an
independent security principal.** Model family diversity is declared,
not authenticated. A generated digest binds only recorded bytes; it does
not independently authenticate the model, reviewer, signer or GPU.

## Local invocation after independent public-source review

From an isolated checkout of `szl-ops-runbook` on BETTERWITHAGE:

```python
from datetime import datetime, timezone
from tools.ollama_peer_crossreview import consult_crossreview, mesh_advisory_packet

# Get repo + SHA from an independently checked GitHub source read.
repo = "szl-holdings/szl-ops-runbook"
sha = "REPLACE_WITH_EXACT_40_CHARACTER_GITHUB_SHA"
evidence = "REPLACE_WITH_HOST_REVIEWED_PUBLIC_SOURCE_EXCERPT_30_PLUS_CHARACTERS"
result = consult_crossreview(
    repo, sha, evidence,
    public_evidence_confirmed=True,
)
print(result["state"], result["reasons"], result["merge_authorized"])
# The optional packet is *declared* evidence for the existing mesh verifier.
# Set patch_sha256 to SHA-256 of the exact owner-reviewed diff bytes.
```

If the model replies include missing/invalid JSON, secret-like strings,
tool calls, duplicated verdict keys, rejection, dissent or abstention, the
cycle **HOLDs**. Neither a successful cross-critique nor a Mesh structural
record is sufficient to merge a PR, grant credentials, deploy to HF/Cloudflare,
publish to PyPI, spend GPUs or change the signed-inference P0.

## Ollama cloud-format recovery (bounded and fail closed)

Ollama's documented structured-output `format` enforcement does **not**
currently apply to cloud-hosted models. A cloud endpoint's textual claim to
output JSON is not a schema guarantee. This adapter therefore parses and
checks the returned bytes independently instead of assuming schema support.

The host requests each critic's `finding` as one sentence of 25–160
characters, while the security gate still admits only the original strict
JSON keys and length limits. A malformed finding, interrupted completion,
or syntactically invalid JSON permits **at most one** retry to that **same**
provider, using the same public peer input and no generated first-failure
response. A second failure remains `HOLD`.

Unsafe content, model tool calls, duplicate keys, unsupported verdicts,
extra authority fields, and contradictory votes are **never** retried or
downgraded. Neither model gets host tools, nor do successful retries create
independent reviewer authentication. The reply receipt records the number
of attempts and the eventual model verdict or fixed refusal reason. Synthetic
tests verify both successful format repair and persistent HOLD.

Official documentation: https://docs.ollama.com/capabilities/structured-outputs

## Negative and independent checks

```powershell
python -B -m unittest discover -s tests -p test_ollama_peer_crossreview.py -v
python -B -m unittest discover -s tests -p test_ollama_peer_consult.py -v
```

Synthetic tests cover: two separate initial model calls and two separate
cross-critiques, explicit dissent/abstention, incomplete first or second
responses, attempted tool calls, duplicate keys, forged authority fields,
secret-like generated output, naive host clocks, missing public-source consent,
and the permanent Mesh `tests=UNAVAILABLE` default.

The adapter's source SHA and test claims are not independently verified by
the models. Do not send private repository patches, production credentials,
patient/customer records, private model weights, private research or
Cloudflare/Snowflake secrets to cloud-hosted Kimi or Mistral. Respect project
licenses, source rights, GitHub protections and the actual reviewer rules.

**No long-running loop is installed.** Invoke each pass under the existing
SZL Ouroboros owner scheduler and stop on no new evidence.
