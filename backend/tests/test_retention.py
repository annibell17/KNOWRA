
import unittest

from app.cognitive_engine.retention import (
    RetentionModel,
    RetentionParameters,
)


class TestRetentionModel(unittest.TestCase):

    def setUp(self):
        self.model = RetentionModel(
            RetentionParameters(
                half_life_days=7,
                minimum_retention=0.05
            )
        )

    def test_retention_at_day_zero(self):
        result = self.model.estimate(0.95, 0)

        self.assertAlmostEqual(
            result["estimated_retention"], 0.95
        )

    def test_retention_halves_above_baseline(self):
        result = self.model.estimate(0.95, 7)

        self.assertAlmostEqual(
            result["estimated_retention"], 0.50
        )

    def test_retention_decreases_over_time(self):
        day_1 = self.model.estimate(0.95, 1)
        day_7 = self.model.estimate(0.95, 7)
        day_14 = self.model.estimate(0.95, 14)

        self.assertGreater(
            day_1["estimated_retention"],
            day_7["estimated_retention"]
        )

        self.assertGreater(
            day_7["estimated_retention"],
            day_14["estimated_retention"]
        )

    def test_retention_stays_above_baseline(self):
        result = self.model.estimate(0.95, 1000)

        self.assertGreaterEqual(
            result["estimated_retention"], 0.05
        )

    def test_negative_elapsed_time_is_rejected(self):
        with self.assertRaises(ValueError):
            self.model.estimate(0.95, -1)

    def test_invalid_half_life_is_rejected(self):
        with self.assertRaises(ValueError):
            RetentionParameters(half_life_days=0)


if __name__ == "__main__":
    unittest.main()

