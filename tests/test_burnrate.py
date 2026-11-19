import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "alerts"))
import yaml
from burnrate import burn_rate, budget_consumed_pct, evaluate, TIERS

ROOT = os.path.join(os.path.dirname(__file__), "..")


class T(unittest.TestCase):
    def test_burn_math(self):
        self.assertAlmostEqual(burn_rate(144, 1000, 0.99), 14.4)
        self.assertEqual(burn_rate(0, 0, 0.99), 0.0)

    def test_budget_pct_matches_workbook_table(self):
        self.assertAlmostEqual(budget_consumed_pct(14.4, 1), 2.0)
        self.assertAlmostEqual(budget_consumed_pct(6, 6), 5.0)
        self.assertAlmostEqual(budget_consumed_pct(1, 72), 10.0)

    def test_rules_yaml_matches_code(self):
        d = yaml.safe_load(open(os.path.join(ROOT, "alerts", "burn_rate_rules.yaml")))
        self.assertEqual([t["burn_rate"] for t in d["tiers"]], [t.burn for t in TIERS])
        for y, c in zip(d["tiers"], TIERS):
            self.assertAlmostEqual(budget_consumed_pct(y["burn_rate"], c.long_h), y["budget_consumed_pct"])

    def w(self, le, lt, se, st, h):
        # same ratio for all long windows / short windows
        return {1.0: (le, lt), 6.0: (le, lt), 72.0: (le, lt), 5 / 60: (se, st), 0.5: (se, st)}

    def test_fires_only_when_both_windows_hot(self):
        # long hot (20% errors), short recovered (0%) -> no page-fast
        r = evaluate(self.w(200, 1000, 0, 100, 0), 0.99)
        self.assertNotIn("page-fast", r)
        self.assertNotIn("page-slow", r)
        # both hot
        self.assertIn("page-fast", evaluate(self.w(200, 1000, 20, 100, 0), 0.99))

    def test_low_traffic_suppressed(self):
        self.assertEqual(evaluate(self.w(5, 10, 5, 10, 0), 0.99), [])

    def test_healthy(self):
        self.assertEqual(evaluate(self.w(1, 1000, 0, 100, 0), 0.99), [])

    def test_slo_file_targets_valid(self):
        d = yaml.safe_load(open(os.path.join(ROOT, "slo", "slos.yaml")))
        for j in d["journeys"]:
            for o in j["objectives"]:
                if "target" in o and o["target"] < 1.0:
                    self.assertTrue(0.9 <= o["target"] < 1.0)


if __name__ == "__main__":
    unittest.main()
