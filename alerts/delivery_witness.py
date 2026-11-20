"""Source-only, non-authorizing classifier for SZL alert delivery observations.

This is not an alert sender, subscriber, receipt verifier, background monitor,
SLO measurement, escalation transport, or a release authority. All inputs are
caller assertions; even an internally coherent success stays UNVERIFIED.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

ACK_BUDGET_MS = 5_000  # good requires strictly less than 5 seconds
SUBSCRIBER_BUDGET_MS = 60_000  # subscriber receipt within 60 seconds
MAX_BATCH = 256
MAX_AGE = timedelta(days=30)
MAX_FUTURE_SKEW = timedelta(minutes=5)
SCHEMA = "szl.alert-delivery-claim.v1"
FIELDS = frozenset(
    {
        "schema",
        "observed_at_utc",
        "relay_http_status",
        "relay_elapsed_ms",
        "subscriber_elapsed_ms",
        "subscriber_correlation_claim",
        "publish_attempts",
        "automatic_retries",
    }
)


def _time(value: object) -> datetime | None:
    if type(value) is not str or not value.endswith("Z") or len(value) > 40:
        return None
    try:
        stamp = datetime.fromisoformat(value)
    except ValueError:
        return None
    return stamp if stamp.tzinfo is not None and stamp.utcoffset() == timedelta(0) else None


def _int_range(value: object, lo: int, hi: int) -> bool:
    return type(value) is int and lo <= value <= hi


def _out(state: str, *, reported_conditions_met: bool = False) -> dict[str, Any]:
    return {
        "schema": "szl.alert-delivery-observation-classification.v1",
        "state": state,
        "reported_conditions_met": reported_conditions_met,
        "subscriber_receipt_independently_verified": False,
        "signed_receipt_verified": False,
        "alert_delivery_verified": False,
        "slo_attested": False,
        "release_authorized": False,
        "automatic_retry_authorized": False,
    }


def evaluate_claim(claim: object, *, now: datetime) -> dict[str, Any]:
    """Check one exact-shape, untrusted claimed response/receipt pair."""
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() != timedelta(0):
        raise ValueError("now must be an aware UTC clock")
    if type(claim) is not dict or set(claim) != FIELDS or claim.get("schema") != SCHEMA:
        return _out("INVALID_CLAIM")
    timestamp = _time(claim["observed_at_utc"])
    if timestamp is None or timestamp - now > MAX_FUTURE_SKEW or now - timestamp > MAX_AGE:
        return _out("UNAVAILABLE_TIMESTAMP")
    attempts = claim["publish_attempts"]
    retries = claim["automatic_retries"]
    if not _int_range(attempts, 1, 1) or not _int_range(retries, 0, 0):
        return _out("UNSAFE_RETRY_OR_AMBIGUOUS_ATTEMPT")
    status = claim["relay_http_status"]
    latency = claim["relay_elapsed_ms"]
    subscriber_latency = claim["subscriber_elapsed_ms"]
    correlated = claim["subscriber_correlation_claim"]
    if status is not None and not _int_range(status, 100, 599):
        return _out("INVALID_HTTP_STATUS")
    if latency is not None and not _int_range(latency, 0, 600_000):
        return _out("INVALID_RELAY_LATENCY")
    if subscriber_latency is not None and not _int_range(subscriber_latency, 0, 600_000):
        return _out("INVALID_SUBSCRIBER_LATENCY")
    if type(correlated) not in (bool, type(None)):
        return _out("INVALID_CORRELATION_CLAIM")
    if status is None or latency is None:
        return _out("UNOBSERVED_RELAY_RESPONSE")
    if status == 429:
        return _out("RATE_LIMITED_NO_RETRY")
    if status == 504:
        return _out("UNKNOWN_DELIVERY_NO_RETRY")
    if status >= 500:
        return _out("UPSTREAM_FAILURE_OR_UNKNOWN_DELIVERY")
    if not 200 <= status <= 299:
        return _out("NON_SUCCESS_RELAY_RESPONSE")
    if latency >= ACK_BUDGET_MS:
        return _out("RELAY_ACK_SLO_BREACH")
    if subscriber_latency is None or correlated is not True:
        return _out("SUBSCRIBER_EVIDENCE_MISSING_OR_UNCORRELATED")
    if subscriber_latency > SUBSCRIBER_BUDGET_MS:
        return _out("SUBSCRIBER_SLO_BREACH")
    return _out("REPORTED_CONDITIONS_MET_NOT_VERIFIED", reported_conditions_met=True)


def summarize_claims(claims: object, *, now: datetime) -> dict[str, Any]:
    """Retain all requested denominators; empty or partial is never healthy."""
    if type(claims) is not list or len(claims) > MAX_BATCH:
        raise ValueError("bounded list of at most 256 observations required")
    observations = [evaluate_claim(c, now=now) for c in claims]
    met = sum(1 for c in observations if c["reported_conditions_met"])
    counts: dict[str, int] = {}
    for c in observations:
        counts[c["state"]] = counts.get(c["state"], 0) + 1
    return {
        "schema": "szl.alert-delivery-window.v1",
        "coverage": "UNOBSERVED" if not observations else "REPORTED_UNVERIFIED",
        "claimed_attempts_observed": len(observations),
        "reported_conditions_met": met,
        "reported_conditions_not_met": len(observations) - met,
        "independently_verified_attempts": 0,
        "independently_verified_delivery_successes": 0,
        "states": dict(sorted(counts.items())),
        "slo_attested": False,
        "production_ready": False,
        "release_authorized": False,
    }


def check_deadline_compatibility(worker_timeout_ms: object) -> dict[str, Any]:
    """Compare configured Worker timeout to adopted <5s acknowledgement budget.

    This is a *design* concern, not proof that any response exceeded the SLO.
    """
    if not _int_range(worker_timeout_ms, 1, 600_000):
        state = "INVALID_WORKER_DEADLINE"
    elif worker_timeout_ms >= ACK_BUDGET_MS:
        state = "WORKER_DEADLINE_CAN_OUTLAST_ACK_SLO"
    else:
        state = "BOUND_WITHIN_ACK_BUDGET_NOT_DELIVERY_PROOF"
    return {
        "state": state,
        "ack_budget_ms_exclusive": ACK_BUDGET_MS,
        "worker_timeout_ms": worker_timeout_ms if type(worker_timeout_ms) is int else None,
        "actual_delivery_verified": False,
        "relay_deployment_verified": False,
    }
