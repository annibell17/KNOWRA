
import math
from dataclasses import dataclass


@dataclass
class RetentionParameters:
    half_life_days: float = 7.0
    minimum_retention: float = 0.05

    def __post_init__(self):
        if self.half_life_days <= 0:
            raise ValueError("Half-life must be greater than zero.")

        if not 0 <= self.minimum_retention <= 1:
            raise ValueError("Minimum retention must be between 0 and 1.")


class RetentionModel:
    """
    Estimates retention decay using an exponential forgetting curve.

    This is an initial configurable model, not an empirically
    calibrated individual memory predictor.
    """

    def __init__(self, parameters=None):
        self.parameters = parameters or RetentionParameters()

    def estimate(self, initial_retention, elapsed_days):
        if not 0 <= initial_retention <= 1:
            raise ValueError("Initial retention must be between 0 and 1.")

        if elapsed_days < 0:
            raise ValueError("Elapsed days cannot be negative.")

        p = self.parameters

        if initial_retention < p.minimum_retention:
            raise ValueError(
                "Initial retention cannot be below minimum retention."
            )

        decay_rate = math.log(2) / p.half_life_days

        retention = (
            p.minimum_retention
            + (initial_retention - p.minimum_retention)
            * math.exp(-decay_rate * elapsed_days)
        )

        return {
            "initial_retention": initial_retention,
            "elapsed_days": elapsed_days,
            "half_life_days": p.half_life_days,
            "estimated_retention": retention,
        }

