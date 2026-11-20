"""Pure fail-closed intake for untrusted Kimi peer-coding suggestions.

No model, shell, network, filesystem writes or release authority.
A positive result is a review candidate, never a signed receipt or admission.
"""
from __future__ import annotations
import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from typing import Any

FIELDS = frozenset({
    "schema", "repo", "head_sha", "path",
    "replacement_line", "negative_cases", "rationale",
})
SCHEMA = "szl.kimi-peer-proposal/v1"
SHA40 = re.compile(r"^[0-9a-f]{40}$")

class PeerProposalHold(ValueError):
    """The untrusted proposal cannot enter the source-only review queue."""

def assess_peer_proposal(
    ollama_reply: Mapping[str, Any],
    *,
    expected_repo: str,
    expected_head_sha: str,
    allowed_paths: Iterable[str],
    approved_replacements: Iterable[str],
    required_negatives: Iterable[str] = ("HOLD", "UNAVAILABLE", "FAILED"),
) -> dict[str, Any]:
    """Bind a model proposal to independently observed source and host allowlists.

    Approved replacements are selected by the host, never the model. Never
    write, run, publish, sign, merge or otherwise act on model-supplied code.
    """
    if not SHA40.fullmatch(expected_head_sha):
        raise PeerProposalHold("INVALID_HOST_SOURCE_PIN")
    if not isinstance(ollama_reply, Mapping):
        raise PeerProposalHold("MODEL_REPLY_NOT_OBJECT")
    message = ollama_reply.get("message")
    if not isinstance(message, Mapping):
        raise PeerProposalHold("MODEL_MESSAGE_MISSING")
    if message.get("tool_calls"):
        raise PeerProposalHold("MODEL_TOOL_CALL_REFUSED")
    content = message.get("content")
    if not isinstance(content, str) or not (2 <= len(content.encode("utf-8")) <= 8192):
        raise PeerProposalHold("MODEL_TEXT_UNAVAILABLE_OR_OVERSIZED")
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        keys = [key for key, _ in pairs]
        if len(keys) != len(set(keys)):
            raise PeerProposalHold("MODEL_JSON_DUPLICATE_KEYS")
        return dict(pairs)

    try:
        proposal = json.loads(content, object_pairs_hook=reject_duplicate_keys)
    except PeerProposalHold:
        raise
    except ValueError as exc:
        raise PeerProposalHold("MODEL_JSON_INVALID") from exc
    if not isinstance(proposal, dict) or set(proposal) != FIELDS:
        raise PeerProposalHold("MODEL_SCHEMA_INVALID")
    if proposal["schema"] != SCHEMA:
        raise PeerProposalHold("MODEL_SCHEMA_VERSION")
    if proposal["repo"] != expected_repo or proposal["head_sha"] != expected_head_sha:
        raise PeerProposalHold("SOURCE_IDENTITY_MISMATCH")
    path = proposal["path"]
    if (
        not isinstance(path, str) or len(path) > 240 or not path
        or path.startswith("/") or "\\" in path or ":" in path
        or any(part in ("", ".", "..") for part in path.split("/"))
        or path not in set(allowed_paths)
    ):
        raise PeerProposalHold("PATH_NOT_ALLOWED")
    replacement = proposal["replacement_line"]
    if not isinstance(replacement, str) or replacement not in set(approved_replacements):
        raise PeerProposalHold("REPLACEMENT_NOT_IN_HOST_ALLOWLIST")
    negatives = proposal["negative_cases"]
    if (
        not isinstance(negatives, list) or len(negatives) > 32
        or any(not isinstance(item, str) or len(item) > 100 for item in negatives)
        or not set(required_negatives).issubset(negatives)
    ):
        raise PeerProposalHold("REQUIRED_NEGATIVE_CONTROLS_MISSING")
    rationale = proposal["rationale"]
    if not isinstance(rationale, str) or not (1 <= len(rationale.strip()) <= 800):
        raise PeerProposalHold("RATIONALE_INVALID")
    canonical = json.dumps(proposal, sort_keys=True, separators=(",", ":"))
    return {
        "decision": "SOURCE_ONLY_REVIEW_CANDIDATE",
        "proposal_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "source_repo": expected_repo,
        "source_head_sha": expected_head_sha,
        "target_path": path,
        "executed": False,
        "source_tests_run": False,
        "independently_reviewed": False,
        "signed_receipt": False,
        "production_admitted": False,
    }
