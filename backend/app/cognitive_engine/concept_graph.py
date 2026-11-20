
from dataclasses import dataclass, field


@dataclass
class Concept:
    concept_id: str
    name: str
    prerequisites: list[str] = field(default_factory=list)
    description: str = ""


class ConceptGraph:
    """
    Directed acyclic graph of learning concepts.

    An edge A -> B means A is a prerequisite for B.
    Concepts must be registered after their prerequisites.
    """

    def __init__(self):
        self.concepts = {}

    def register_concept(self, concept):
        if concept.concept_id in self.concepts:
            raise ValueError("Concept ID already registered.")

        if not concept.concept_id.strip():
            raise ValueError("Concept ID cannot be empty.")

        if not concept.name.strip():
            raise ValueError("Concept name cannot be empty.")

        if len(concept.prerequisites) != len(set(concept.prerequisites)):
            raise ValueError("Duplicate prerequisites are not allowed.")

        if concept.concept_id in concept.prerequisites:
            raise ValueError("A concept cannot depend on itself.")

        for prerequisite in concept.prerequisites:
            if prerequisite not in self.concepts:
                raise ValueError(
                    f"Unknown prerequisite: {prerequisite}"
                )

        self.concepts[concept.concept_id] = concept

    def get_concept(self, concept_id):
        if concept_id not in self.concepts:
            raise ValueError("Unknown concept ID.")

        return self.concepts[concept_id]

    def get_prerequisites(self, concept_id):
        concept = self.get_concept(concept_id)
        return list(concept.prerequisites)

    def get_learning_path(self, target_concept_id):
        """
        Return prerequisites in learning order,
        followed by the target concept.
        """

        self.get_concept(target_concept_id)

        visited = set()
        visiting = set()
        learning_path = []

        def visit(concept_id):
            if concept_id in visiting:
                raise ValueError("Cycle detected in concept graph.")

            if concept_id in visited:
                return

            visiting.add(concept_id)

            concept = self.get_concept(concept_id)

            for prerequisite in concept.prerequisites:
                visit(prerequisite)

            visiting.remove(concept_id)
            visited.add(concept_id)
            learning_path.append(concept_id)

        visit(target_concept_id)

        return learning_path

    def get_missing_prerequisites(
        self,
        target_concept_id,
        mastered_concepts
    ):
        """
        Return unmastered prerequisites in learning order.
        The target concept itself is excluded.
        """

        learning_path = self.get_learning_path(target_concept_id)

        prerequisites = learning_path[:-1]

        return [
            concept_id
            for concept_id in prerequisites
            if concept_id not in mastered_concepts
        ]
