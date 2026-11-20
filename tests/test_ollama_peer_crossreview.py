# SPDX-License-Identifier: Apache-2.0
"""No-network adversarial tests for host-owned Kimi x Mistral cross review."""
from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from ollama_peer_crossreview import (  # noqa: E402
    PeerConsultHold,
    consult_crossreview,
    mesh_advisory_packet,
)

SOURCE = "a" * 40
PATCH = "b" * 64
REPO = "szl-holdings/szl-ops-runbook"
PUBLIC = (
    "Public source evidence: the source-only peer review adapter has no "
    "cross-review stage and cannot validate model disagreement. No secrets."
)
NOW = datetime(2026, 11, 20, 6, 35, tzinfo=timezone.utc)
TEXT = {
    "kimi-k3.1-pro:cloud": (
        "Independent Kimi analysis: require pinned source and separate model "
        "critic. Test forged reviews and all unknown test results fail closed."
    ),
    "mistral-large-4:cloud": (
        "Independent Mistral analysis: a green test cannot authenticate "
        "a reviewer. Reject automated merge and preserve all release gates."
    ),
}


def finished(content, *, reason="stop", tool_calls=None):
    msg = {"content": content}
    if tool_calls is not None:
        msg["tool_calls"] = tool_calls
    return {"done": True, "done_reason": reason, "message": msg}


def vote(verdict="APPROVE", reason_code="NO_FINDINGS", finding=None):
    finding = finding or (
        "Verified only as a synthetic review. Still require external "
        "source pin and test receipt before any release."
    )
    return finished(json.dumps({
        "verdict": verdict, "reason_code": reason_code, "finding": finding,
    }))


def fixture(overrides=None):
    calls = []
    overrides = overrides or {}

    def transport(model, prompt):
        stage = "cross" if "opponent_text_json=" in prompt else "first"
        calls.append((stage, model, prompt))
        result = overrides.get((stage, model))
        if result is not None:
            return result
        if stage == "first":
            return finished(TEXT[model])
        return vote(
            finding="This model independently checked a second opinion "
            + model + " against the stated source-only refusal criteria."
        )

    return calls, transport


def assess(transport):
    return consult_crossreview(
        REPO, SOURCE, PUBLIC, public_evidence_confirmed=True,
        transport=transport, now=NOW,
    )


class CrossReviewTests(unittest.TestCase):
    def test_four_calls_two_distinct_models_and_no_merger(self):
        calls, transport = fixture()
        out = assess(transport)
        self.assertEqual([(stage, model) for stage, model, _ in calls], [
            ("first", "kimi-k3.1-pro:cloud"),
            ("first", "mistral-large-4:cloud"),
            ("cross", "kimi-k3.1-pro:cloud"),
            ("cross", "mistral-large-4:cloud"),
        ])
        self.assertEqual(out["state"], "ADVISORY_CYCLE_COMPLETE_HOST_TESTS_REQUIRED")
        for k in ("merge_authorized", "execution_authorized",
                  "deployment_authorized", "production_ready",
                  "models_authenticity_verified", "host_tests_verified",
                  "signed_receipt"):
            self.assertIs(out[k], False)
        self.assertEqual(out["model_tool_calls_granted"], 0)
        self.assertIn("opponent_text_json=", calls[2][2])
        self.assertNotIn(TEXT["mistral-large-4:cloud"], calls[2][2].split(
            "opponent_text_json=", 1)[0])

    def test_one_first_round_failure_blocks_cross_review(self):
        calls, transport = fixture({
            ("first", "mistral-large-4:cloud"): finished("", reason="length"),
        })
        out = assess(transport)
        self.assertEqual(out["state"], "HOLD")
        self.assertEqual(out["reasons"], ["INDEPENDENT_ROUND_UNAVAILABLE"])
        self.assertEqual(len(calls), 2)

    def test_model_output_secret_does_not_reach_other_cloud_model(self):
        unsafe = TEXT["mistral-large-4:cloud"] + (
            " Authorization: Bearer private_dummy_token_do_not_forward"
        )
        calls, transport = fixture({
            ("first", "mistral-large-4:cloud"): finished(unsafe),
        })
        out = assess(transport)
        self.assertEqual(out["state"], "HOLD")
        self.assertIn("UNTRUSTED_PEER_TEXT_NOT_FORWARDABLE", out["reasons"])
        self.assertEqual(len(calls), 2)
        self.assertFalse(out["merge_authorized"])
        self.assertNotIn("private_dummy_token_do_not_forward", str(out))
        self.assertIsNotNone(out["independent_round"]["reviews"][1]["response_sha256"])
        self.assertNotIn("response", out["independent_round"]["reviews"][1])

    def test_peer_dissent_fails_closed(self):
        calls, transport = fixture({
            ("cross", "mistral-large-4:cloud"): vote(
                "REJECT", "SECURITY_RISK", "Model output could forge a CI green "
                "badge without reading protected source.",
            )
        })
        out = assess(transport)
        self.assertEqual(out["state"], "HOLD")
        self.assertIn("PEER_DISSENT", out["reasons"])
        self.assertEqual(len(calls), 4)

    def test_abstention_never_becomes_approval(self):
        calls, transport = fixture({
            ("cross", "kimi-k3.1-pro:cloud"): vote(
                "ABSTAIN", "INSUFFICIENT_EVIDENCE",
                "No independent signer or runtime source binding was observed."
            )
        })
        out = assess(transport)
        self.assertEqual(out["state"], "HOLD")
        self.assertIn("PEER_ABSTAINED", out["reasons"])

    def test_second_round_tool_calls_are_refused(self):
        calls, transport = fixture({
            ("cross", "mistral-large-4:cloud"): finished(
                vote()["message"]["content"], tool_calls=[{"name": "shell"}],
            )
        })
        out = assess(transport)
        self.assertEqual(out["state"], "HOLD")
        self.assertIn("CROSS_REVIEW_UNAVAILABLE", out["reasons"])
        self.assertEqual(out["cross_reviews"][1]["error_code"],
                         "CROSS_REVIEW_TOOLS_REFUSED")

    def test_duplicate_keys_even_equal_rejected(self):
        raw = ('{"verdict":"APPROVE","reason_code":"NO_FINDINGS",'
               '"finding":"Sufficient synthetic rationale; no release right.",'
               '"verdict":"APPROVE"}')
        calls, transport = fixture({
            ("cross", "kimi-k3.1-pro:cloud"): finished(raw),
        })
        out = assess(transport)
        self.assertEqual(out["state"], "HOLD")
        self.assertEqual(out["cross_reviews"][0]["error_code"],
                         "CROSS_REVIEW_DUPLICATE_JSON_KEY")

    def test_extra_authority_field_refused(self):
        extra = json.loads(vote()["message"]["content"])
        extra["merge_authorized"] = True
        calls, transport = fixture({
            ("cross", "kimi-k3.1-pro:cloud"): finished(json.dumps(extra)),
        })
        out = assess(transport)
        self.assertIn("CROSS_REVIEW_UNAVAILABLE", out["reasons"])
        self.assertFalse(out["merge_authorized"])

    def test_public_confirmation_required_before_model_calls(self):
        calls, transport = fixture()
        with self.assertRaisesRegex(PeerConsultHold,
                                    "PUBLIC_SOURCE_CONFIRMATION_REQUIRED"):
            consult_crossreview(
                REPO, SOURCE, PUBLIC, public_evidence_confirmed=False,
                transport=transport, now=NOW,
            )
        self.assertEqual(calls, [])

    def test_naive_host_clock_refused_before_any_call(self):
        calls, transport = fixture()
        with self.assertRaisesRegex(PeerConsultHold, "HOST_CLOCK_REQUIRED"):
            consult_crossreview(
                REPO, SOURCE, PUBLIC, public_evidence_confirmed=True,
                transport=transport, now=datetime(2026, 11, 20),
            )
        self.assertEqual(calls, [])

    def test_mesh_packet_keeps_independent_tests_unavailable(self):
        _, transport = fixture()
        out = assess(transport)
        packet = mesh_advisory_packet(out, patch_sha256=PATCH)
        self.assertEqual(packet["schema"], "szl.mesh.peer-code-review-advisory/v1")
        self.assertEqual(packet["source_sha"], SOURCE)
        self.assertEqual(packet["tests"]["status"], "UNAVAILABLE")
        self.assertEqual(packet["tests"]["passed"], 0)
        self.assertEqual(packet["tests"]["failed"], 0)
        self.assertEqual([x["provider_family"] for x in packet["reviewers"]],
                         ["MOONSHOT", "MISTRAL"])

    def test_mesh_packet_invalid_patch_refused(self):
        _, transport = fixture()
        out = assess(transport)
        with self.assertRaisesRegex(PeerConsultHold, "HOST_PATCH_SHA_INVALID"):
            mesh_advisory_packet(out, patch_sha256="main")


if __name__ == "__main__":
    unittest.main()
