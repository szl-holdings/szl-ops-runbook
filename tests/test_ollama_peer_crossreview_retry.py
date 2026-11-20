# SPDX-License-Identifier: Apache-2.0
"""Independent transport + real-package-path tests for bounded format repair."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.ollama_peer_crossreview import consult_crossreview  # noqa: E402

REPO = "szl-holdings/szl-ops-runbook"
SOURCE = "a" * 40
EVIDENCE = (
    "This is public GitHub source evidence for a bounded, no-tool "
    "Kimi and Mistral cross-review process; outputs cannot grant a merge."
)
NOW = datetime(2026, 11, 20, 7, 10, tzinfo=timezone.utc)
FIRST = {
    "kimi-k3.1-pro:cloud": (
        "Kimi independently proposes refusing a forged source or model identity, "
        "even if the user or two reviewers request an automatic production merge."
    ),
    "mistral-large-4:cloud": (
        "Mistral independently proposes stale reviewer and unsigned source tests "
        "and explicitly denies that a model opinion is an independent approval."
    ),
}
FINDING = "A model verdict is not a signed source or production-runtime attestation."


def response(text: str, *, tool_calls=None, done_reason="stop"):
    message = {"content": text}
    if tool_calls is not None:
        message["tool_calls"] = tool_calls
    return {"done": True, "done_reason": done_reason, "message": message}


def structured(*, verdict="APPROVE", reason="NO_FINDINGS",
               finding=FINDING, extra=None):
    body = {"verdict": verdict, "reason_code": reason, "finding": finding}
    if extra:
        body.update(extra)
    return response(json.dumps(body))


def run_transport(overrides=None):
    calls = []
    overrides = overrides or {}

    def transport(model, prompt):
        is_cross = "opponent_text_json=" in prompt
        stage = "cross" if is_cross else "initial"
        attempts = sum(row[:2] == (stage, model) for row in calls) + 1
        calls.append((stage, model, prompt))
        if (stage, model, attempts) in overrides:
            return overrides[(stage, model, attempts)]
        if is_cross:
            return structured()
        return response(FIRST[model])

    out = consult_crossreview(
        REPO, SOURCE, EVIDENCE, public_evidence_confirmed=True,
        transport=transport, now=NOW,
    )
    return out, calls


def test_single_format_retry_yields_advisory_not_merger():
    out, calls = run_transport({
        ("cross", "kimi-k3.1-pro:cloud", 1): structured(finding="short"),
    })
    assert out["state"] == "ADVISORY_CYCLE_COMPLETE_HOST_TESTS_REQUIRED"
    assert len(calls) == 5
    assert out["cross_reviews"][0]["attempts"] == 2
    assert out["cross_reviews"][1]["attempts"] == 1
    assert "FORMAT_RETRY_ONLY" in calls[3][2]
    for flag in ("merge_authorized", "execution_authorized",
                 "deployment_authorized", "production_ready", "signed_receipt"):
        assert out[flag] is False


def test_persistently_invalid_findings_hold_after_one_retry():
    out, calls = run_transport({
        ("cross", "kimi-k3.1-pro:cloud", 1): structured(finding="short"),
        ("cross", "kimi-k3.1-pro:cloud", 2): structured(finding="short"),
    })
    assert out["state"] == "HOLD"
    assert out["reasons"] == ["CROSS_REVIEW_UNAVAILABLE"]
    assert out["cross_reviews"][0]["error_code"] == "CROSS_REVIEW_FINDING_INVALID"
    assert out["cross_reviews"][0]["attempts"] == 2
    assert len(calls) == 5


def test_incomplete_and_non_json_can_retry_with_same_model_only():
    cases = (response("", done_reason="length"), response("not-json" * 6))
    for invalid in cases:
        out, calls = run_transport({
            ("cross", "mistral-large-4:cloud", 1): invalid,
        })
        assert out["state"] == "ADVISORY_CYCLE_COMPLETE_HOST_TESTS_REQUIRED"
        assert len(calls) == 5
        assert calls[-1][1] == "mistral-large-4:cloud"
        assert out["cross_reviews"][1]["attempts"] == 2


def test_duplicate_key_is_not_retried_or_normalized():
    invalid = response(
        '{"verdict":"APPROVE","verdict":"APPROVE","reason_code":'
        '"NO_FINDINGS","finding":"Sufficient synthetic rationale; no release right."}'
    )
    out, calls = run_transport({("cross", "kimi-k3.1-pro:cloud", 1): invalid})
    assert out["state"] == "HOLD"
    assert out["cross_reviews"][0]["attempts"] == 1
    assert out["cross_reviews"][0]["error_code"] == "CROSS_REVIEW_DUPLICATE_JSON_KEY"
    assert len(calls) == 4


def test_tool_call_and_forged_authority_not_retried():
    for bad in (
        response(structured()["message"]["content"], tool_calls=[{"name": "shell"}]),
        structured(extra={"merge_authorized": True}),
    ):
        out, calls = run_transport({
            ("cross", "mistral-large-4:cloud", 1): bad,
        })
        assert out["state"] == "HOLD"
        assert out["cross_reviews"][1]["attempts"] == 1
        assert len(calls) == 4


def test_dissent_survives_permitted_format_retry():
    out, calls = run_transport({
        ("cross", "kimi-k3.1-pro:cloud", 1): structured(finding="short"),
        ("cross", "kimi-k3.1-pro:cloud", 2): structured(
            verdict="REJECT", reason="SECURITY_RISK",
            finding="A green CI result can never authenticate a cloud model's weights.",
        ),
    })
    assert out["state"] == "HOLD"
    assert out["cross_reviews"][0]["verdict"] == "REJECT"
    assert "PEER_DISSENT" in out["reasons"]
    assert len(calls) == 5
