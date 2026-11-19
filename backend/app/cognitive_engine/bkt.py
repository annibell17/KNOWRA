
from dataclasses import dataclass


@dataclass
class BKTParameters:
    """
    Parameters for Bayesian Knowledge Tracing.

    These are initial illustrative values, not experimentally
    calibrated parameters for KNOWRA.
    """
    initial_knowledge: float = 0.20
    learning_probability: float = 0.15
    guess_probability: float = 0.20
    slip_probability: float = 0.10

    def __post_init__(self):
        values = [
            self.initial_knowledge,
            self.learning_probability,
            self.guess_probability,
            self.slip_probability,
        ]

        if any(not 0 <= value <= 1 for value in values):
            raise ValueError("All BKT parameters must be between 0 and 1.")


class BayesianKnowledgeTracer:
    """
    Estimates the probability that a learner knows a concept
    using Bayesian Knowledge Tracing.
    """

    def __init__(self, parameters=None):
        self.parameters = parameters or BKTParameters()

    def update(self, prior_knowledge, correct):
        p = self.parameters

        # Probability of a correct response before observing the answer
        p_correct = (
            prior_knowledge * (1 - p.slip_probability)
            + (1 - prior_knowledge) * p.guess_probability
        )

        if correct:
            numerator = prior_knowledge * (1 - p.slip_probability)
            denominator = p_correct
        else:
            numerator = prior_knowledge * p.slip_probability
            denominator = 1 - p_correct

        if denominator == 0:
            raise ValueError("Cannot update from an impossible observation.")

        # Bayesian update after observing the response
        posterior = numerator / denominator

        # Account for learning between practice opportunities
        updated_knowledge = (
            posterior
            + (1 - posterior) * p.learning_probability
        )

        return {
            "prior_knowledge": prior_knowledge,
            "probability_correct": p_correct,
            "posterior_knowledge": posterior,
            "updated_knowledge": updated_knowledge,
            "response": "correct" if correct else "incorrect",
        }

    def trace_sequence(self, responses):
        """
        Process a sequence of boolean responses.

        True = correct
        False = incorrect
        """
        knowledge = self.parameters.initial_knowledge
        history = []

        for index, response in enumerate(responses, start=1):
            result = self.update(knowledge, response)
            result["attempt"] = index
            history.append(result)

            knowledge = result["updated_knowledge"]

        return history

