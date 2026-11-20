<!-- SPDX-License-Identifier: Apache-2.0 -->

# Bounded Kimi × Mistral consultation (advisory only)

`tools/ollama_peer_consult.py` is an intentionally small, standard-library-only
adapter for two **independent** public-source code reviews through a local
Ollama gateway. It does not delegate tools, execute model output, write files,
approve PRs, publish artifacts, or authorize releases.

## Prerequisites

- An Ollama server on `http://127.0.0.1:11434`. The transport rejects
  HTTP redirects and ignores ambient HTTP(S) proxy variables. If a gateway
  requires a redirect to work, treat that as HOLD rather than following it.
- Working `kimi-k3.1-pro:cloud` and `mistral-large-4:cloud` aliases.
- An operator-verified **public** repository excerpt and exact 40-character
  GitHub source commit. **No secrets, private code, command lines, or keys.**
- Explicit `public_evidence_confirmed=True` after reviewing the excerpt.

The Mistral request uses the chat interface with `think: false` and
`num_predict: 1800`. A tiny generation budget previously produced an empty
final response after spending the token allowance on thinking. The adapter
fails closed on incomplete output rather than treating it as an approval.

## Example

```python
from tools.ollama_peer_consult import consult_public_peer_review

result = consult_public_peer_review(
    "szl-holdings/szl-ops-runbook",
    "<exact-current-40-character-github-commit>",  # replace with real SHA
    "Public source excerpt and the independently observed failure, at least 30 characters.",
    public_evidence_confirmed=True,
)
assert result["merge_authorized"] is False
print(result["decision"])
```

Run deterministic contract tests with
`python -m unittest discover -s tests -p test_ollama_peer_consult.py -v`.

## Release and privacy boundary

- Loopback smoke tests use synthetic requests and isolated local HTTP servers:
  a 302 redirect never reaches the second origin, and hostile `HTTP_PROXY`
  settings never receive the prompt. These tests do not prove a compromised
  host or Ollama process cannot intercept requests.
- The caller **must** independently re-read GitHub's head SHA and CI checks
  before any proposed patch is considered. The adapter explicitly marks
  `source_freshness_independently_verified=False`.
- `CONSULTED_NOT_EXECUTED` confirms that both reviewers returned text, **not**
  that either answer is correct or tests passed. Any missing model, interrupted
  generation, or model tool-call request yields `HOLD`.
- `evidence_sha256` binds the input text for comparison. It is **not** a
  cryptographic signature or deployment receipt.
- `provider_write_state=NOT_MEASURED` is deliberately not an assurance
  about arbitrary caller-injected transports; no model or adapter release
  authority is granted. The numeric adapter release-action count is local,
  not an externally audited provider-write receipt.
- The token-pattern filter is defense in depth, **not** a secret scanner.
  Only operator-reviewed public evidence should be sent to cloud models.
- Apply host-owned allowlists, regression tests, signed provenance where
  required, and GitHub's existing protections in a separate release lane.
