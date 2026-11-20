"""Deterministic adversarial controls for advisory Kimi peer intake."""
import json
import pytest
from tools.kimi_peer_gate import PeerProposalHold, assess_peer_proposal

REPO = "szl-holdings/szl-ops-runbook"
SHA = "a" * 40
PATH = "tools/candidate.py"
SAFE = 'return isinstance(state, str) and state.strip().upper() == "ADMITTED"'

def payload(**updates):
    obj = {
        "schema": "szl.kimi-peer-proposal/v1",
        "repo": REPO,
        "head_sha": SHA,
        "path": PATH,
        "replacement_line": SAFE,
        "negative_cases": ["HOLD", "UNAVAILABLE", "FAILED"],
        "rationale": "Require exact state, never a truthy non-empty string.",
    }
    obj.update(updates)
    return {"message": {"content": json.dumps(obj)}}

def assess(response):
    return assess_peer_proposal(
        response, expected_repo=REPO, expected_head_sha=SHA,
        allowed_paths=[PATH], approved_replacements=[SAFE])

def test_safe_response_stays_advisory():
    result = assess(payload())
    assert result["decision"] == "SOURCE_ONLY_REVIEW_CANDIDATE"
    assert result["source_head_sha"] == SHA
    for field in ("executed", "source_tests_run", "independently_reviewed",
                  "signed_receipt", "production_admitted"):
        assert result[field] is False

@pytest.mark.parametrize(("response", "code"), [
    (payload(head_sha="b" * 40), "SOURCE_IDENTITY_MISMATCH"),
    (payload(repo="other-owner/other-repo"), "SOURCE_IDENTITY_MISMATCH"),
    (payload(path="../.env"), "PATH_NOT_ALLOWED"),
    (payload(path=r"C:\secrets\env"), "PATH_NOT_ALLOWED"),
    (payload(path="tools/other.py"), "PATH_NOT_ALLOWED"),
    (payload(replacement_line="return __import__('os').system('whoami')"), "REPLACEMENT_NOT_IN_HOST_ALLOWLIST"),
    (payload(negative_cases=["READY", "MAYBE"]), "REQUIRED_NEGATIVE_CONTROLS_MISSING"),
    (payload(production_admitted=True), "MODEL_SCHEMA_INVALID"),
    ({"message": {"content": "The model is a part of the second brain. " * 30}}, "MODEL_JSON_INVALID"),
    ({"message": {"content": json.dumps(json.loads(payload()["message"]["content"])),
                  "tool_calls": [{"function": {"name": "shell"}}]}}, "MODEL_TOOL_CALL_REFUSED"),
])
def test_fail_closed_controls(response, code):
    with pytest.raises(PeerProposalHold, match=code):
        assess(response)

def test_duplicate_model_json_keys_fail_closed_even_if_equal_or_escaped():
    original = payload()["message"]["content"]
    for extra in (
        '"path": "tools/candidate.py"',
        '"path": "../.env"',
        r'"\u0070ath": "tools/candidate.py"',
    ):
        duplicate = original[:-1] + ", " + extra + "}"
        with pytest.raises(PeerProposalHold, match="MODEL_JSON_DUPLICATE_KEYS"):
            assess({"message": {"content": duplicate}})


def test_host_sha_must_be_exact():
    with pytest.raises(PeerProposalHold, match="INVALID_HOST_SOURCE_PIN"):
        assess_peer_proposal(payload(), expected_repo=REPO, expected_head_sha="main",
                             allowed_paths=[PATH], approved_replacements=[SAFE])

def test_model_cannot_invent_test_or_signature_evidence():
    obj = json.loads(payload()["message"]["content"])
    obj["source_tests_run"] = True
    with pytest.raises(PeerProposalHold, match="MODEL_SCHEMA_INVALID"):
        assess({"message": {"content": json.dumps(obj)}})
