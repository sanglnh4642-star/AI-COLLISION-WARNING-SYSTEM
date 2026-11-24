
"""
test_scenarios.py
KIEM THU CAC TINH HUONG MO PHONG

Kiem thu module: simulation/scenarios.py
Thu vien: unittest
"""

import sys
import unittest
from pathlib import Path

# Xac dinh thu muc goc cua du an
ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from simulation.scenarios import (
    get_all_scenarios,
    get_scenario_by_id
)


class TestScenarios(unittest.TestCase):

    # ------------------------------------------------------
    # 1. Kiem tra lay danh sach tinh huong
    # ------------------------------------------------------
    def test_get_all_scenarios(self):
        scenarios = get_all_scenarios()

        self.assertIsInstance(scenarios, list)
        self.assertGreater(len(scenarios), 0)

    # ------------------------------------------------------
    # 2. Kiem tra so luong tinh huong
    # ------------------------------------------------------
    def test_scenario_count(self):
        scenarios = get_all_scenarios()

        self.assertEqual(len(scenarios), 4)

    # ------------------------------------------------------
    # 3. Kiem tra ID cac tinh huong
    # ------------------------------------------------------
    def test_scenario_ids(self):
        scenarios = get_all_scenarios()

        ids = [scenario["id"] for scenario in scenarios]

        self.assertEqual(ids, [1, 2, 3, 4])

    # ------------------------------------------------------
    # 4. Kiem tra du lieu cac tinh huong
    # ------------------------------------------------------
    def test_scenario_data(self):
        expected = {
            1: (30, 50),
            2: (60, 50),
            3: (72, 30),
            4: (90, 25)
        }

        scenarios = get_all_scenarios()

        for scenario in scenarios:
            scenario_id = scenario["id"]

            self.assertIn(scenario_id, expected)
            self.assertEqual(
                scenario["speed"],
                expected[scenario_id][0]
            )
            self.assertEqual(
                scenario["distance"],
                expected[scenario_id][1]
            )

    # ------------------------------------------------------
    # 5. Kiem tra cac truong du lieu bat buoc
    # ------------------------------------------------------
    def test_required_fields(self):
        scenarios = get_all_scenarios()

        required_fields = [
            "id",
            "name",
            "description",
            "speed",
            "distance"
        ]

        for scenario in scenarios:
            for field in required_fields:
                self.assertIn(field, scenario)

    # ------------------------------------------------------
    # 6. Kiem tra tim tinh huong theo ID
    # ------------------------------------------------------
    def test_get_scenario_by_id(self):
        scenario = get_scenario_by_id(1)

        self.assertIsNotNone(scenario)
        self.assertEqual(scenario["id"], 1)
        self.assertEqual(scenario["speed"], 30)
        self.assertEqual(scenario["distance"], 50)

    # ------------------------------------------------------
    # 7. Kiem tra tim cac tinh huong con lai
    # ------------------------------------------------------
    def test_get_all_scenarios_by_id(self):
        for scenario_id in range(1, 5):
            scenario = get_scenario_by_id(scenario_id)

            self.assertEqual(scenario["id"], scenario_id)

    # ------------------------------------------------------
    # 8. Kiem tra ID khong ton tai
    # ------------------------------------------------------
    def test_invalid_scenario_id(self):
        with self.assertRaises(ValueError):
            get_scenario_by_id(999)

    # ------------------------------------------------------
    # 9. Kiem tra danh sach tra ve la ban sao
    # ------------------------------------------------------
    def test_scenarios_are_copied(self):
        scenarios = get_all_scenarios()

        original_name = get_all_scenarios()[0]["name"]

        scenarios[0]["name"] = "Du lieu kiem thu"

        new_scenarios = get_all_scenarios()

        self.assertEqual(
            new_scenarios[0]["name"],
            original_name
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
