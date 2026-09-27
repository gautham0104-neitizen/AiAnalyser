from __future__ import annotations

from typing import Dict


class MLFeatureBuilder:
    """
    Converts programmer behavior analysis into
    a numerical feature vector suitable for ML models.
    """

    def build(self, behavior: Dict) -> Dict[str, float]:

        if not behavior.get("valid"):
            raise ValueError(
                "Invalid behavior analysis."
            )

        scores = behavior["scores"]
        metrics = behavior["metrics"]

        return {
            # -----------------------------
            # Code quality
            # -----------------------------

            "average_complexity":
                float(metrics["average_complexity"]),

            "average_maintainability":
                float(metrics["average_maintainability"]),

            # -----------------------------
            # Coding behavior
            # -----------------------------

            "nested_loop_percentage":
                float(metrics["nested_loop_percentage"]),

            "recursion_percentage":
                float(metrics["recursion_percentage"]),

            # -----------------------------
            # Behavioral scores
            # -----------------------------

            "algorithm_diversity":
                float(scores["algorithm_diversity"]),

            "data_structure_diversity":
                float(scores["data_structure_diversity"]),

            "brute_force_tendency":
                float(scores["brute_force_tendency"]),

            "optimization_score":
                float(scores["optimization"]),

            "code_quality_score":
                float(scores["code_quality"]),

            "problem_solving_diversity":
                float(
                    scores["problem_solving_diversity"]
                ),

            "improvement_score":
                float(scores["improvement"])
        }