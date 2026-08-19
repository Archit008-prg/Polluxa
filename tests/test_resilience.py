import unittest
from scripts.demo_resilience import (
    demo_scenario_1_idempotent_recovery,
    demo_scenario_2_malformed_input,
    demo_scenario_3_end_to_end_refresh
)

class TestResilienceSuite(unittest.TestCase):
    def test_scenarios(self):
        demo_scenario_1_idempotent_recovery()
        demo_scenario_2_malformed_input()
        demo_scenario_3_end_to_end_refresh()

if __name__ == "__main__":
    unittest.main()
