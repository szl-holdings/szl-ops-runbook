"""Synthetic alert observations; no network, sending, secrets or subscriber calls."""

from __future__ import annotations

import unittest
from copy import deepcopy
from datetime import UTC, datetime

from alerts.delivery_witness import (
    ACK_BUDGET_MS,
    SCHEMA,
    SUBSCRIBER_BUDGET_MS,
    check_deadline_compatibility,
    evaluate_claim,
    summarize_claims,
)

NOW = datetime(2026, 11, 20, 6, 10, tzinfo=UTC)


def claim() -> dict:
    return {
        "schema": SCHEMA,
        "observed_at_utc": "2026-11-20T06:10:00Z",
        "relay_http_status": 200,
        "relay_elapsed_ms": 280,
        "subscriber_elapsed_ms": 820,
        "subscriber_correlation_claim": True,
        "publish_attempts": 1,
        "automatic_retries": 0,
    }


class DeliveryWitnessTests(unittest.TestCase):
    def verdict(self, **updates):
        c = claim()
        c.update(updates)
        return evaluate_claim(c, now=NOW)

    def assert_not_admitted(self, r):
        self.assertFalse(r["alert_delivery_verified"])
        self.assertFalse(r["signed_receipt_verified"])
        self.assertFalse(r["slo_attested"])
        self.assertFalse(r["release_authorized"])
        self.assertFalse(r["automatic_retry_authorized"])

    def test_reported_200_with_subscriber_claim_never_authenticates(self):
        r = self.verdict()
        self.assertEqual(r["state"], "REPORTED_CONDITIONS_MET_NOT_VERIFIED")
        self.assertTrue(r["reported_conditions_met"])
        self.assert_not_admitted(r)

    def test_provider_429_rate_limit(self):
        r = self.verdict(relay_http_status=429)
        self.assertEqual(r["state"], "RATE_LIMITED_NO_RETRY")
        self.assert_not_admitted(r)

    def test_unknown_504_not_auto_retried(self):
        r = self.verdict(relay_http_status=504)
        self.assertEqual(r["state"], "UNKNOWN_DELIVERY_NO_RETRY")
        self.assert_not_admitted(r)

    def test_timeout_502_not_false_delivered(self):
        r = self.verdict(relay_http_status=502)
        self.assertEqual(r["state"], "UPSTREAM_FAILURE_OR_UNKNOWN_DELIVERY")
        self.assert_not_admitted(r)

    def test_other_server_errors_hold(self):
        for code in (500, 503, 599):
            with self.subTest(code=code):
                r = self.verdict(relay_http_status=code)
                self.assertEqual(r["state"], "UPSTREAM_FAILURE_OR_UNKNOWN_DELIVERY")

    def test_302_redirect_not_success(self):
        self.assertEqual(self.verdict(relay_http_status=302)["state"], "NON_SUCCESS_RELAY_RESPONSE")

    def test_402_payment_required_not_success(self):
        self.assertEqual(self.verdict(relay_http_status=402)["state"], "NON_SUCCESS_RELAY_RESPONSE")

    def test_http_ack_strict_five_second_boundary(self):
        good = self.verdict(relay_elapsed_ms=ACK_BUDGET_MS - 1)
        bad = self.verdict(relay_elapsed_ms=ACK_BUDGET_MS)
        self.assertTrue(good["reported_conditions_met"])
        self.assertEqual(bad["state"], "RELAY_ACK_SLO_BREACH")

    def test_25_second_worker_timeout_exceeds_slo(self):
        r = check_deadline_compatibility(25_000)
        self.assertEqual(r["state"], "WORKER_DEADLINE_CAN_OUTLAST_ACK_SLO")
        self.assertFalse(r["actual_delivery_verified"])

    def test_bounded_deadline_not_a_delivery_receipt(self):
        r = check_deadline_compatibility(4000)
        self.assertEqual(r["state"], "BOUND_WITHIN_ACK_BUDGET_NOT_DELIVERY_PROOF")
        self.assertFalse(r["relay_deployment_verified"])

    def test_invalid_deadlines(self):
        for value in (0, -1, True, None, "4000", 600001):
            with self.subTest(value=value):
                self.assertEqual(check_deadline_compatibility(value)["state"], "INVALID_WORKER_DEADLINE")

    def test_missing_subscriber_receipt(self):
        self.assertEqual(
            self.verdict(subscriber_elapsed_ms=None)["state"],
            "SUBSCRIBER_EVIDENCE_MISSING_OR_UNCORRELATED",
        )

    def test_uncorrelated_subscriber_receipt(self):
        self.assertEqual(
            self.verdict(subscriber_correlation_claim=False)["state"],
            "SUBSCRIBER_EVIDENCE_MISSING_OR_UNCORRELATED",
        )

    def test_subscriber_within_sixty_seconds_inclusive(self):
        r = self.verdict(subscriber_elapsed_ms=SUBSCRIBER_BUDGET_MS)
        self.assertTrue(r["reported_conditions_met"])
        self.assert_not_admitted(r)

    def test_subscriber_after_sixty_seconds(self):
        self.assertEqual(
            self.verdict(subscriber_elapsed_ms=SUBSCRIBER_BUDGET_MS + 1)["state"],
            "SUBSCRIBER_SLO_BREACH",
        )

    def test_no_publication_observed(self):
        self.assertEqual(self.verdict(relay_http_status=None)["state"], "UNOBSERVED_RELAY_RESPONSE")

    def test_no_relay_latency(self):
        self.assertEqual(self.verdict(relay_elapsed_ms=None)["state"], "UNOBSERVED_RELAY_RESPONSE")

    def test_retry_duplicate_is_prohibited(self):
        for times, automatic in ((2, 1), (1, 1), (0, 0), (3, 2)):
            with self.subTest(times=times, automatic=automatic):
                self.assertEqual(
                    self.verdict(publish_attempts=times, automatic_retries=automatic)["state"],
                    "UNSAFE_RETRY_OR_AMBIGUOUS_ATTEMPT",
                )

    def test_boolean_not_numeric_http_status(self):
        self.assertEqual(self.verdict(relay_http_status=True)["state"], "INVALID_HTTP_STATUS")

    def test_non_numeric_latency(self):
        self.assertEqual(self.verdict(relay_elapsed_ms="10")["state"], "INVALID_RELAY_LATENCY")

    def test_negative_subscriber_latency(self):
        self.assertEqual(self.verdict(subscriber_elapsed_ms=-1)["state"], "INVALID_SUBSCRIBER_LATENCY")

    def test_boolean_correlation_type(self):
        self.assertEqual(self.verdict(subscriber_correlation_claim=1)["state"], "INVALID_CORRELATION_CLAIM")

    def test_missing_field_fails_closed(self):
        c = claim()
        del c["subscriber_elapsed_ms"]
        self.assertEqual(evaluate_claim(c, now=NOW)["state"], "INVALID_CLAIM")

    def test_fake_signed_authority_field_fails_closed(self):
        c = claim()
        c["signature_verified"] = True
        self.assertEqual(evaluate_claim(c, now=NOW)["state"], "INVALID_CLAIM")

    def test_bad_utc_stamp(self):
        self.assertEqual(
            self.verdict(observed_at_utc="2026-11-20T01:10:00-05:00")["state"],
            "UNAVAILABLE_TIMESTAMP",
        )

    def test_stale_and_future_observation(self):
        for stamp in ("2026-10-01T00:00:00Z", "2026-11-20T06:16:00Z"):
            with self.subTest(stamp=stamp):
                self.assertEqual(self.verdict(observed_at_utc=stamp)["state"], "UNAVAILABLE_TIMESTAMP")

    def test_invalid_clock_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_claim(claim(), now=datetime(2026, 11, 20, 6, 10))

    def test_empty_batch_is_unobserved(self):
        result = summarize_claims([], now=NOW)
        self.assertEqual(result["coverage"], "UNOBSERVED")
        self.assertEqual(result["claimed_attempts_observed"], 0)
        self.assertFalse(result["production_ready"])

    def test_mixed_batch_denominators_are_not_green(self):
        rows = [claim() for _ in range(3)]
        rows[1]["relay_http_status"] = 429
        rows[2]["subscriber_elapsed_ms"] = None
        result = summarize_claims(rows, now=NOW)
        self.assertEqual(result["claimed_attempts_observed"], 3)
        self.assertEqual(result["reported_conditions_met"], 1)
        self.assertEqual(result["reported_conditions_not_met"], 2)
        self.assertEqual(result["independently_verified_attempts"], 0)
        self.assertFalse(result["production_ready"])

    def test_all_reported_good_still_unverified(self):
        result = summarize_claims([claim(), claim()], now=NOW)
        self.assertEqual(result["reported_conditions_met"], 2)
        self.assertEqual(result["coverage"], "REPORTED_UNVERIFIED")
        self.assertFalse(result["slo_attested"])

    def test_batch_size_bounded(self):
        with self.assertRaises(ValueError):
            summarize_claims([claim()] * 257, now=NOW)

    def test_source_claim_is_not_modified(self):
        c = claim()
        before = deepcopy(c)
        evaluate_claim(c, now=NOW)
        self.assertEqual(c, before)


if __name__ == "__main__":
    unittest.main()
