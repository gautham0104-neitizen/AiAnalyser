from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np

from backend.analyzer.ast_analyzer import CodeAnalyzer
from backend.analyzer.complexity import ComplexityAnalyzer
from ml.feature_builder import MLFeatureBuilder


class InferenceEngine:

    FEATURE_NAMES = [
        "average_complexity",
        "average_maintainability",
        "nested_loop_percentage",
        "recursion_percentage",
        "algorithm_diversity",
        "data_structure_diversity",
        "brute_force_tendency",
        "optimization_score",
        "code_quality_score",
        "problem_solving_diversity",
        "improvement_score"
    ]

    def __init__(self):

        # -------------------------------------------------
        # MODEL PATHS
        # -------------------------------------------------

        project_root = (
            Path(__file__).resolve().parent.parent
        )

        self.model_path = (
            project_root
            / "models"
            / "kmeans_model.pkl"
        )

        self.scaler_path = (
            project_root
            / "models"
            / "scaler.pkl"
        )

        # -------------------------------------------------
        # LOAD TRAINED MODEL
        # -------------------------------------------------

        if not self.model_path.exists():

            raise FileNotFoundError(
                f"K-Means model not found: "
                f"{self.model_path}"
            )

        if not self.scaler_path.exists():

            raise FileNotFoundError(
                f"Scaler not found: "
                f"{self.scaler_path}"
            )

        with open(
            self.model_path,
            "rb"
        ) as file:

            self.model = pickle.load(
                file
            )

        with open(
            self.scaler_path,
            "rb"
        ) as file:

            self.scaler = pickle.load(
                file
            )

        # -------------------------------------------------
        # ANALYZERS
        # -------------------------------------------------

        self.ast_analyzer = CodeAnalyzer()

        self.complexity_analyzer = (
            ComplexityAnalyzer()
        )

        self.feature_builder = (
            MLFeatureBuilder()
        )

    # =====================================================
    # ANALYZE CODE
    # =====================================================

    def analyze_code(
        self,
        code: str
    ):

        # -------------------------------------------------
        # AST ANALYSIS
        # -------------------------------------------------

        ast_result = (
            self.ast_analyzer.analyze(
                code
            )
        )

        if not ast_result["valid"]:

            return {
                "valid": False,
                "error": ast_result["error"]
            }

        # -------------------------------------------------
        # COMPLEXITY ANALYSIS
        # -------------------------------------------------

        complexity_result = (
            self.complexity_analyzer.analyze(
                code
            )
        )

        if not complexity_result["valid"]:

            return {
                "valid": False,
                "error": complexity_result["error"]
            }

        # -------------------------------------------------
        # CODE-LEVEL FEATURES
        # -------------------------------------------------

        features = {

            "average_complexity":
                complexity_result[
                    "cyclomatic_complexity"
                ]["average"],

            "average_maintainability":
                complexity_result[
                    "maintainability_index"
                ],

            "nested_loop_percentage":
                100
                if ast_result.get(
                    "nested_loops",
                    0
                ) > 0
                else 0,

            "recursion_percentage":
                100
                if ast_result.get(
                    "recursive_functions",
                    0
                ) > 0
                else 0,

            "algorithm_diversity":
                self._calculate_algorithm_diversity(
                    ast_result
                ),

            "data_structure_diversity":
                self._calculate_data_structure_diversity(
                    ast_result
                ),

            "brute_force_tendency":
                self._calculate_brute_force(
                    ast_result
                ),

            "optimization_score":
                self._calculate_optimization(
                    ast_result,
                    complexity_result
                ),

            "code_quality_score":
                complexity_result[
                    "maintainability_index"
                ],

            "problem_solving_diversity":
                self._calculate_problem_solving_diversity(
                    ast_result
                ),

            "improvement_score":
                0.0
        }

        return {
            "valid": True,
            "ast": ast_result,
            "complexity": complexity_result,
            "features": features
        }

    # =====================================================
    # FEATURE HELPERS
    # =====================================================

    def _calculate_algorithm_diversity(
        self,
        features
    ):

        patterns = features.get(
            "patterns",
            []
        )

        count = len(patterns)

        return min(
            100.0,
            count * 20.0
        )

    # -----------------------------------------------------

    def _calculate_data_structure_diversity(
        self,
        features
    ):

        structures = features.get(
            "data_structures",
            {}
        )

        if not isinstance(
            structures,
            dict
        ):

            return 0.0

        count = 0

        for key, value in structures.items():

            if key.endswith(
                "_usage"
            ):

                if (
                    isinstance(
                        value,
                        (int, float)
                    )
                    and value > 0
                ):

                    count += 1

            elif key.endswith(
                "_detected"
            ):

                if value:

                    count += 1

        return min(
            100.0,
            count * 20.0
        )

    # -----------------------------------------------------

    def _calculate_brute_force(
        self,
        features
    ):

        nested = features.get(
            "nested_loops",
            0
        )

        total_loops = features.get(
            "total_loops",
            0
        )

        if nested > 0:

            return 80.0

        if total_loops > 1:

            return 40.0

        return 0.0

    # -----------------------------------------------------

    def _calculate_optimization(
        self,
        features,
        complexity
    ):

        score = 0.0

        patterns = features.get(
            "patterns",
            []
        )

        pattern_text = str(
            patterns
        ).lower()

        if (
            "hash_map" in pattern_text
            or "two_pointer" in pattern_text
            or "binary_search" in pattern_text
            or "sliding_window" in pattern_text
        ):

            score += 40

        if features.get(
            "nested_loops",
            0
        ) == 0:

            score += 20

        maintainability = complexity.get(
            "maintainability_index",
            0
        )

        if maintainability >= 70:

            score += 20

        if (
            complexity
            .get(
                "cyclomatic_complexity",
                {}
            )
            .get(
                "average",
                0
            )
            <= 4
        ):

            score += 20

        return min(
            100.0,
            score
        )

    # -----------------------------------------------------

    def _calculate_problem_solving_diversity(
        self,
        features
    ):

        score = 0.0

        patterns = str(
            features.get(
                "patterns",
                []
            )
        ).lower()

        if patterns:

            score += 30

        if features.get(
            "num_functions",
            0
        ) > 1:

            score += 20

        if features.get(
            "num_variables",
            0
        ) > 3:

            score += 20

        if features.get(
            "total_loops",
            0
        ) > 0:

            score += 15

        if features.get(
            "conditional_expressions",
            0
        ) > 0:

            score += 15

        return min(
            100.0,
            score
        )

    # =====================================================
    # ML VECTOR
    # =====================================================

    def build_vector(
        self,
        analysis
    ):

        if not analysis["valid"]:

            raise ValueError(
                analysis["error"]
            )

        features = analysis[
            "features"
        ]

        return np.array(
            [
                features[name]
                for name in self.FEATURE_NAMES
            ],
            dtype=float
        ).reshape(
            1,
            -1
        )

    # =====================================================
    # ML PREDICTION
    # =====================================================

    def predict(
        self,
        analysis
    ):

        vector = self.build_vector(
            analysis
        )

        # Apply the SAME scaler used
        # during model training.

        scaled_vector = (
            self.scaler.transform(
                vector
            )
        )

        # Predict cluster.

        cluster = int(
            self.model.predict(
                scaled_vector
            )[0]
        )

        # Calculate distances from the
        # new code to every cluster center.

        distances = (
            self.model.transform(
                scaled_vector
            )[0]
        )

        # Convert distances into a sharper
        # similarity distribution.
        #
        # Smaller distance = stronger membership.

        temperature = 2.0

        similarities = np.exp(
            -distances / temperature
        )

        memberships = (
            similarities
            / similarities.sum()
        )

        return {
            "cluster": cluster,
            "memberships": memberships,
            "vector": vector,
            "scaled_vector": scaled_vector
        }

    # =====================================================
    # PREDICT FROM FEATURES
    # =====================================================

    def predict_features(
        self,
        features
    ):

        vector = np.array(
            [
                features[name]
                for name in self.FEATURE_NAMES
            ],
            dtype=float
        ).reshape(1, -1)

        scaled_vector = (
            self.scaler.transform(
                vector
            )
        )

        predicted_cluster = int(
            self.model.predict(
                scaled_vector
            )[0]
        )

        distances = (
            self.model.transform(
                scaled_vector
            )[0]
        )

        temperature = 2.0

        similarities = np.exp(
            -distances / temperature
        )

        memberships = (
            similarities
            / similarities.sum()
        )

        return (
            predicted_cluster,
            memberships
        )