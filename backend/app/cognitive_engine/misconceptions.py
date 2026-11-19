
from dataclasses import dataclass


@dataclass
class MisconceptionRule:
    option_id: str
    misconception_id: str
    description: str
    confidence: float = 1.0


@dataclass
class DiagnosticQuestion:
    question_id: str
    concept_id: str
    correct_option_id: str
    misconception_rules: list


class MisconceptionDetector:
    """
    Rule-based misconception detection.

    Diagnoses only errors explicitly mapped to a question.
    Unknown answers are not assigned invented explanations.
    """

    def __init__(self, questions=None):
        self.questions = questions or {}

    def register_question(self, question):
        if question.question_id in self.questions:
            raise ValueError("Question ID already registered.")

        option_ids = [
            rule.option_id
            for rule in question.misconception_rules
        ]

        if len(option_ids) != len(set(option_ids)):
            raise ValueError("Duplicate diagnostic option IDs.")

        if question.correct_option_id in option_ids:
            raise ValueError(
                "Correct option cannot be a misconception option."
            )

        for rule in question.misconception_rules:
            if not 0 <= rule.confidence <= 1:
                raise ValueError("Confidence must be between 0 and 1.")

        self.questions[question.question_id] = question

    def diagnose(self, question_id, selected_option_id):
        question = self.questions.get(question_id)

        if question is None:
            raise ValueError("Unknown question ID.")

        if selected_option_id == question.correct_option_id:
            return {
                "question_id": question_id,
                "concept_id": question.concept_id,
                "is_correct": True,
                "diagnosis": None,
                "message": "Correct answer.",
            }

        for rule in question.misconception_rules:
            if selected_option_id == rule.option_id:
                return {
                    "question_id": question_id,
                    "concept_id": question.concept_id,
                    "is_correct": False,
                    "diagnosis": rule.misconception_id,
                    "description": rule.description,
                    "confidence": rule.confidence,
                    "message": "A mapped misconception was detected.",
                }

        return {
            "question_id": question_id,
            "concept_id": question.concept_id,
            "is_correct": False,
            "diagnosis": None,
            "message": "Incorrect answer; insufficient evidence for diagnosis.",
        }
