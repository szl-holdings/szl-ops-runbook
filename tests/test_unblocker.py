"""Offline classification regressions: never invoke gh or provider operations."""
import datetime as dt
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "unblocker", Path(__file__).resolve().parents[1] / "tools" / "unblocker.py"
)
unblocker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(unblocker)
NOW = dt.datetime(2026, 11, 2, tzinfo=dt.timezone.utc)


def pr(**changes):
    value = dict(repo="szl-holdings/example", number=1, title="Repair",
                 url="https://github.com/szl-holdings/example/pull/1", isDraft=False,
                 mergeable="MERGEABLE", mergeStateStatus="CLEAN",
                 reviewDecision="APPROVED", reviewRequests=[], body="",
                 updatedAt="2026-11-01T00:00:00Z", additions=1, deletions=1,
                 changedFiles=1, statusCheckRollup=[
                     dict(name="tests", status="COMPLETED", conclusion="SUCCESS")])
    value.update(changes)
    return value


class ClassificationTests(unittest.TestCase):
    def setUp(self):
        guard = patch.object(unblocker, "gh", side_effect=AssertionError("offline only"))
        guard.start()
        self.addCleanup(guard.stop)

    def classes(self, value):
        return {b["class"] for b in unblocker.classify(value, NOW)["blockers"]}

    def test_successful_clean_snapshot_is_ready_for_owner_review(self):
        self.assertEqual(self.classes(pr()), {"READY"})

    def test_pending_checks_never_ready(self):
        for status in ("QUEUED", "IN_PROGRESS", "PENDING", "WAITING", "REQUESTED", "PENDING_DEPLOYMENT"):
            with self.subTest(status=status):
                self.assertNotIn("READY", self.classes(pr(statusCheckRollup=[dict(name="tests", status=status)])))

    def test_pending_legacy_status_never_ready(self):
        self.assertNotIn("READY", self.classes(pr(statusCheckRollup=[dict(context="tests", state="PENDING")])))

    def test_missing_checks_never_ready(self):
        for checks in (None, [], {}, "unavailable"):
            with self.subTest(checks=checks):
                self.assertNotIn("READY", self.classes(pr(statusCheckRollup=checks)))

    def test_malformed_checks_never_ready(self):
        for check in (None, "SUCCESS", {}, dict(name="tests", status="COMPLETED"),
                      dict(name="tests", status="COMPLETED", conclusion="NEW_RESULT"),
                      dict(name="tests", status=123)):
            with self.subTest(check=check):
                self.assertNotIn("READY", self.classes(pr(statusCheckRollup=[check])))

    def test_neutral_or_skipped_only_is_not_green(self):
        for result in ("NEUTRAL", "SKIPPED"):
            with self.subTest(result=result):
                self.assertNotIn("READY", self.classes(pr(statusCheckRollup=[dict(name="tests", status="COMPLETED", conclusion=result)])))

    def test_success_with_skipped_optional_check(self):
        value = pr()
        value["statusCheckRollup"].append(dict(name="publish", status="COMPLETED", conclusion="SKIPPED"))
        self.assertIn("READY", self.classes(value))

    def test_success_with_unknown_check_never_ready(self):
        value = pr()
        value["statusCheckRollup"].append({})
        self.assertNotIn("READY", self.classes(value))

    def test_legacy_success_supported(self):
        self.assertIn("READY", self.classes(pr(statusCheckRollup=[dict(context="legacy", state="SUCCESS")])))

    def test_success_requires_completed_execution_evidence(self):
        for status in (None, "", False, 0):
            with self.subTest(status=status):
                self.assertNotIn("READY", self.classes(pr(statusCheckRollup=[dict(name="tests", status=status, conclusion="SUCCESS")])))
        self.assertNotIn("READY", self.classes(pr(statusCheckRollup=[dict(name="tests", conclusion="SUCCESS")])))

    def test_mixed_check_and_legacy_shapes_are_unknown(self):
        for check in (dict(name="tests", conclusion="SUCCESS", state="SUCCESS"),
                      dict(context="legacy", state="FAILURE", conclusion="SUCCESS")):
            with self.subTest(check=check):
                self.assertNotIn("READY", self.classes(pr(statusCheckRollup=[check])))

    def test_blocking_review_decisions(self):
        for decision in ("CHANGES_REQUESTED", "REVIEW_REQUIRED", "UNKNOWN"):
            with self.subTest(decision=decision):
                self.assertNotIn("READY", self.classes(pr(reviewDecision=decision)))

    def test_outstanding_review_request_blocks_regardless_of_age(self):
        for decision in (None, "APPROVED"):
            with self.subTest(decision=decision):
                self.assertNotIn("READY", self.classes(pr(reviewDecision=decision, reviewRequests=[{"login": "reviewer"}])))

    def test_no_review_requirement_is_not_invented(self):
        self.assertIn("READY", self.classes(pr(reviewDecision=None)))

    def test_only_clean_merge_state_is_ready(self):
        for state in ("UNSTABLE", "HAS_HOOKS", "UNKNOWN", "BLOCKED", "BEHIND", "DIRTY"):
            with self.subTest(state=state):
                self.assertNotIn("READY", self.classes(pr(mergeStateStatus=state)))

    def test_unknown_mergeability_is_visible_blocker(self):
        classes = self.classes(pr(mergeable="UNKNOWN"))
        self.assertTrue(classes)
        self.assertNotIn("READY", classes)

    def test_existing_failure_mapping_preserved(self):
        for name, expected in (("Security Gate", "SECURITY_GATE"), ("Run tests", "TESTS_RED"), ("szl/provenance", "PROVENANCE_BODY")):
            with self.subTest(name=name):
                classes = self.classes(pr(statusCheckRollup=[dict(name=name, status="COMPLETED", conclusion="FAILURE")]))
                self.assertIn(expected, classes)
                self.assertNotIn("READY", classes)

    def test_draft_and_hold_remain_blocked(self):
        self.assertIn("DRAFT_GATE", self.classes(pr(isDraft=True)))
        self.assertIn("HOLD", self.classes(pr(title="HOLD: owner decision")))

    def test_pending_remains_visible_alongside_failure(self):
        row = unblocker.classify(pr(statusCheckRollup=[dict(name="tests", status="COMPLETED", conclusion="FAILURE"), dict(name="lint", status="QUEUED")]), NOW)
        self.assertEqual(row["pending"], 1)
        self.assertIn("CHECKS_PENDING", {b["class"] for b in row["blockers"]})

    def test_board_does_not_authorize_merge(self):
        rendered = unblocker.board([unblocker.classify(pr(), NOW)], "szl-holdings", NOW)
        self.assertNotIn("ready to merge", rendered.lower())
        self.assertNotIn("squash-merge", rendered.lower())
        self.assertIn("owner review", rendered.lower())


if __name__ == "__main__":
    unittest.main()
