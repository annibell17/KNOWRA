import json
from dataclasses import dataclass
from pathlib import Path

from .cognitive_engine.concept_graph import Concept, ConceptGraph
from .cognitive_engine.misconceptions import (
    DiagnosticQuestion,
    MisconceptionDetector,
    MisconceptionRule,
)


DATA_DIR = Path(__file__).parent / "data"


@dataclass
class LearningContent:
    """All content and cognitive structures for one learning module."""

    module_id: str
    title: str
    description: str
    concept_graph: ConceptGraph
    misconception_detector: MisconceptionDetector
    questions: dict


def _read_json(path: Path) -> dict:
    """Read a JSON file and ensure its root is an object."""

    if not path.is_file():
        raise FileNotFoundError(f"Content file not found: {path}")

    with path.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path.name}.")

    return data


def load_learning_content(
    concepts_path: Path | None = None,
    questions_path: Path | None = None,
) -> LearningContent:
    """Load a learning module and its question bank."""

    concepts_path = concepts_path or (
        DATA_DIR / "math_concepts" / "algebra.json"
    )

    questions_path = questions_path or (
        DATA_DIR / "questions" / "algebra_linear_equations.json"
    )

    concept_data = _read_json(Path(concepts_path))
    question_data = _read_json(Path(questions_path))

    module_id = concept_data.get("module_id")

    if not module_id:
        raise ValueError("Learning module must have a module_id.")

    if question_data.get("module_id") != module_id:
        raise ValueError("Concept and question module IDs do not match.")

    graph = ConceptGraph()
    concepts = concept_data.get("concepts")

    if not isinstance(concepts, list) or not concepts:
        raise ValueError("Learning module must contain concepts.")

    for item in concepts:
        if not isinstance(item, dict):
            raise ValueError("Each concept must be a JSON object.")

        graph.register_concept(
            Concept(
                concept_id=item["concept_id"],
                name=item["name"],
                description=item.get("description", ""),
                prerequisites=item.get("prerequisites", []),
            )
        )

    detector = MisconceptionDetector()
    learner_questions = {}
    question_records = question_data.get("questions")

    if not isinstance(question_records, list) or not question_records:
        raise ValueError("Question bank must contain questions.")

    for item in question_records:
        if not isinstance(item, dict):
            raise ValueError("Each question must be a JSON object.")

        question_id = item["question_id"]
        concept_id = item["concept_id"]
        prompt = item["prompt"]
        options = item["options"]
        correct_option_id = item["correct_option_id"]

        if concept_id not in graph.concepts:
            raise ValueError(
                f"Question {question_id} references unknown concept: "
                f"{concept_id}"
            )

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"Question {question_id} has an empty prompt.")

        if not isinstance(options, list) or len(options) < 2:
            raise ValueError(
                f"Question {question_id} must have at least two options."
            )

        option_ids = []

        for option in options:
            if not isinstance(option, dict):
                raise ValueError(
                    f"Question {question_id} has an invalid option."
                )

            option_id = option.get("option_id")
            option_text = option.get("text")

            if not isinstance(option_id, str) or not option_id.strip():
                raise ValueError(
                    f"Question {question_id} has an invalid option ID."
                )

            if not isinstance(option_text, str) or not option_text.strip():
                raise ValueError(
                    f"Question {question_id} has an empty option."
                )

            option_ids.append(option_id)

        if len(option_ids) != len(set(option_ids)):
            raise ValueError(
                f"Question {question_id} has duplicate option IDs."
            )

        if correct_option_id not in option_ids:
            raise ValueError(
                f"Question {question_id} has no matching correct option."
            )

        rules = []

        for rule in item.get("misconception_rules", []):
            if rule["option_id"] not in option_ids:
                raise ValueError(
                    f"Misconception rule in {question_id} references "
                    f"an unknown option: {rule['option_id']}"
                )

            rules.append(
                MisconceptionRule(
                    option_id=rule["option_id"],
                    misconception_id=rule["misconception_id"],
                    description=rule["description"],
                    confidence=rule.get("confidence", 1.0),
                )
            )

        diagnostic_question = DiagnosticQuestion(
            question_id=question_id,
            concept_id=concept_id,
            correct_option_id=correct_option_id,
            misconception_rules=rules,
        )

        detector.register_question(diagnostic_question)

        learner_questions[question_id] = {
            "question_id": question_id,
            "concept_id": concept_id,
            "difficulty": item.get("difficulty", "unspecified"),
            "type": item.get("type", "multiple_choice"),
            "prompt": prompt,
            "options": options,
            "correct_option_id": correct_option_id,
            "explanation": item.get("explanation", ""),
            "tags": item.get("tags", []),
        }

    return LearningContent(
        module_id=module_id,
        title=concept_data.get("title", module_id),
        description=concept_data.get("description", ""),
        concept_graph=graph,
        misconception_detector=detector,
        questions=learner_questions,
    )
