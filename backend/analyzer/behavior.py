from __future__ import annotations

import json
from typing import Any, Dict, List


class BehaviorAnalyzer:
    """
    Phase 4 v3 — Programmer Behavior Analyzer.

    Analyzes a programmer's submission history to determine:

    - Algorithm diversity
    - Data-structure diversity
    - Brute-force tendency
    - Optimization ability
    - Code quality
    - Complexity trend
    - Maintainability trend
    - Learning/improvement trend
    - Strengths
    - Weaknesses
    - Recommendations

    This is rule-based.
    Machine learning is introduced in Phase 5.
    """

    def analyze(self, submissions: List[Any]) -> Dict[str, Any]:

        if not submissions:
            return {
                "valid": False,
                "error": "No submissions available."
            }

        # ---------------------------------------------------------
        # Sort chronologically
        # ---------------------------------------------------------

        submissions = sorted(
            submissions,
            key=lambda row: row["submitted_at"]
        )

        total = len(submissions)

        # ---------------------------------------------------------
        # Counters
        # ---------------------------------------------------------

        pattern_counts = {}
        data_structure_counts = {}

        complexity_values = []
        maintainability_values = []

        nested_loop_submissions = 0
        recursive_submissions = 0

        # ---------------------------------------------------------
        # Process submissions
        # ---------------------------------------------------------

        for submission in submissions:

            complexity = (
                submission["cyclomatic_complexity"] or 0
            )

            maintainability = (
                submission["maintainability_index"] or 0
            )

            complexity_values.append(complexity)
            maintainability_values.append(maintainability)

            if (submission["nested_loops"] or 0) > 0:
                nested_loop_submissions += 1

            if (submission["recursive_functions"] or 0) > 0:
                recursive_submissions += 1

            # -----------------------------
            # Patterns
            # -----------------------------

            patterns = self._parse_json(
                submission,
                "patterns",
                []
            )

            for pattern in patterns:

                if isinstance(pattern, dict):

                    name = pattern.get("pattern")

                    if name:
                        pattern_counts[name] = (
                            pattern_counts.get(name, 0) + 1
                        )

            # -----------------------------
            # Data structures
            # -----------------------------

            structures = self._parse_json(
                submission,
                "data_structures",
                {}
            )

            if isinstance(structures, dict):

                for name, value in structures.items():

                    if isinstance(value, bool):

                        if value:
                            data_structure_counts[name] = (
                                data_structure_counts.get(name, 0)
                                + 1
                            )

                    elif isinstance(value, (int, float)):

                        if value > 0:
                            data_structure_counts[name] = (
                                data_structure_counts.get(name, 0)
                                + 1
                            )

        # ---------------------------------------------------------
        # Basic metrics
        # ---------------------------------------------------------

        average_complexity = round(
            sum(complexity_values) / total,
            2
        )

        average_maintainability = round(
            sum(maintainability_values) / total,
            2
        )

        nested_loop_percentage = round(
            nested_loop_submissions / total * 100,
            2
        )

        recursion_percentage = round(
            recursive_submissions / total * 100,
            2
        )

        # ---------------------------------------------------------
        # Diversity
        # ---------------------------------------------------------

        algorithm_diversity = (
            self._algorithm_diversity_score(
                pattern_counts,
                total
            )
        )

        data_structure_diversity = (
            self._data_structure_diversity_score(
                data_structure_counts,
                total
            )
        )

        problem_solving_diversity = round(
            algorithm_diversity * 0.6
            + data_structure_diversity * 0.4,
            2
        )

        # ---------------------------------------------------------
        # Current scores
        # ---------------------------------------------------------

        brute_force_score = self._brute_force_score(
            nested_loop_percentage,
            average_complexity,
            pattern_counts,
            total
        )

        optimization_score = self._optimization_score(
            average_complexity,
            pattern_counts,
            data_structure_counts,
            total
        )

        code_quality_score = self._code_quality_score(
            average_maintainability,
            average_complexity
        )

        # ---------------------------------------------------------
        # Trend analysis
        # ---------------------------------------------------------

        trend = self._calculate_trends(
            complexity_values,
            maintainability_values,
            submissions
        )

        # ---------------------------------------------------------
        # Improvement score
        # ---------------------------------------------------------

        improvement_score = self._improvement_score(
            trend
        )

        # ---------------------------------------------------------
        # Style
        # ---------------------------------------------------------

        style, style_reason = self._determine_style(
            brute_force_score,
            optimization_score,
            algorithm_diversity,
            data_structure_diversity,
            recursion_percentage
        )

        # ---------------------------------------------------------
        # Strengths
        # ---------------------------------------------------------

        strengths = self._find_strengths(
            algorithm_diversity,
            data_structure_diversity,
            optimization_score,
            code_quality_score,
            improvement_score,
            recursion_percentage
        )

        # ---------------------------------------------------------
        # Weaknesses
        # ---------------------------------------------------------

        weaknesses = self._find_weaknesses(
            brute_force_score,
            optimization_score,
            algorithm_diversity,
            data_structure_diversity,
            average_complexity,
            pattern_counts
        )

        # ---------------------------------------------------------
        # Recommendations
        # ---------------------------------------------------------

        recommendations = self._generate_recommendations(
            brute_force_score,
            optimization_score,
            algorithm_diversity,
            data_structure_diversity,
            average_complexity,
            pattern_counts,
            trend
        )

        # ---------------------------------------------------------
        # Final result
        # ---------------------------------------------------------

        return {
            "valid": True,

            "submissions_analyzed": total,

            "programming_style": {
                "name": style,
                "reason": style_reason
            },

            "scores": {
                "algorithm_diversity":
                    algorithm_diversity,

                "data_structure_diversity":
                    data_structure_diversity,

                "brute_force_tendency":
                    brute_force_score,

                "optimization":
                    optimization_score,

                "code_quality":
                    code_quality_score,

                "problem_solving_diversity":
                    problem_solving_diversity,

                "improvement":
                    improvement_score
            },

            "metrics": {
                "average_complexity":
                    average_complexity,

                "average_maintainability":
                    average_maintainability,

                "nested_loop_percentage":
                    nested_loop_percentage,

                "recursion_percentage":
                    recursion_percentage,

                "algorithm_patterns":
                    pattern_counts,

                "data_structures":
                    data_structure_counts
            },

            "trends": trend,

            "strengths": strengths,

            "weaknesses": weaknesses,

            "recommendations": recommendations
        }

    # ============================================================
    # ALGORITHM DIVERSITY
    # ============================================================

    def _algorithm_diversity_score(
        self,
        pattern_counts,
        total
    ):

        if not pattern_counts:
            return 0

        unique_patterns = len(pattern_counts)

        # Diversity score considers both variety and usage.
        variety_score = min(
            unique_patterns / 8 * 70,
            70
        )

        repeated_patterns = sum(
            1
            for count in pattern_counts.values()
            if count >= 2
        )

        usage_score = min(
            repeated_patterns / 4 * 30,
            30
        )

        return round(
            min(variety_score + usage_score, 100),
            2
        )

    # ============================================================
    # DATA STRUCTURE DIVERSITY
    # ============================================================

    def _data_structure_diversity_score(
        self,
        counts,
        total
    ):

        useful = {
            "list_usage",
            "dict_usage",
            "set_usage",
            "stack_detected",
            "queue_detected",
            "heap_detected"
        }

        score = 0

        for structure in useful:

            usage = counts.get(structure, 0)

            if usage >= total * 0.5:
                score += 20

            elif usage >= total * 0.25:
                score += 15

            elif usage > 0:
                score += 8

        return round(
            min(score, 100),
            2
        )

    # ============================================================
    # BRUTE FORCE
    # ============================================================

    def _brute_force_score(
        self,
        nested_loop_percentage,
        average_complexity,
        pattern_counts,
        total
    ):

        score = 0

        score += nested_loop_percentage * 0.5

        if average_complexity >= 6:
            score += 25

        elif average_complexity >= 5:
            score += 18

        elif average_complexity >= 4:
            score += 10

        brute_force_count = pattern_counts.get(
            "brute_force",
            0
        )

        score += (
            brute_force_count / total
        ) * 30

        return round(
            min(score, 100),
            2
        )

    # ============================================================
    # OPTIMIZATION
    # ============================================================

    def _optimization_score(
        self,
        average_complexity,
        pattern_counts,
        data_structure_counts,
        total
    ):

        score = 0

        # Complexity
        if average_complexity <= 2:
            score += 40

        elif average_complexity <= 3:
            score += 32

        elif average_complexity <= 4:
            score += 24

        elif average_complexity <= 5:
            score += 12

        efficient_patterns = {
            "binary_search",
            "two_pointers",
            "sliding_window",
            "hash_map_lookup",
            "dynamic_programming"
        }

        efficient_usage = sum(
            pattern_counts.get(
                pattern,
                0
            )
            for pattern in efficient_patterns
        )

        score += min(
            efficient_usage / total * 45,
            45
        )

        # Hash maps / sets
        if data_structure_counts.get(
            "dict_usage",
            0
        ) > 0:

            score += 7

        if data_structure_counts.get(
            "set_usage",
            0
        ) > 0:

            score += 8

        return round(
            min(score, 100),
            2
        )

    # ============================================================
    # CODE QUALITY
    # ============================================================

    def _code_quality_score(
        self,
        maintainability,
        average_complexity
    ):

        score = maintainability

        if average_complexity >= 8:
            score -= 20

        elif average_complexity >= 6:
            score -= 10

        elif average_complexity >= 4:
            score -= 5

        return round(
            max(min(score, 100), 0),
            2
        )

    # ============================================================
    # TREND ANALYSIS
    # ============================================================

    def _calculate_trends(
        self,
        complexity_values,
        maintainability_values,
        submissions
    ):

        total = len(complexity_values)

        if total < 4:

            return {
                "available": False,
                "message":
                    "At least 4 submissions are needed "
                    "for meaningful trend analysis."
            }

        split = total // 2

        early_complexity = (
            sum(complexity_values[:split])
            / split
        )

        recent_complexity = (
            sum(complexity_values[split:])
            / (total - split)
        )

        early_maintainability = (
            sum(maintainability_values[:split])
            / split
        )

        recent_maintainability = (
            sum(maintainability_values[split:])
            / (total - split)
        )

        complexity_change = (
            early_complexity
            - recent_complexity
        )

        maintainability_change = (
            recent_maintainability
            - early_maintainability
        )

        # Percentage improvement in complexity.
        if early_complexity != 0:

            complexity_improvement = (
                complexity_change
                / early_complexity
                * 100
            )

        else:
            complexity_improvement = 0

        return {
            "available": True,

            "early_complexity":
                round(early_complexity, 2),

            "recent_complexity":
                round(recent_complexity, 2),

            "complexity_improvement":
                round(complexity_improvement, 2),

            "early_maintainability":
                round(early_maintainability, 2),

            "recent_maintainability":
                round(recent_maintainability, 2),

            "maintainability_change":
                round(maintainability_change, 2)
        }

    # ============================================================
    # IMPROVEMENT SCORE
    # ============================================================

    def _improvement_score(self, trend):

        if not trend.get("available"):
            return 50

        score = 50

        complexity_improvement = (
            trend["complexity_improvement"]
        )

        maintainability_change = (
            trend["maintainability_change"]
        )

        score += complexity_improvement * 0.5
        score += maintainability_change * 1.5

        return round(
            max(min(score, 100), 0),
            2
        )

    # ============================================================
    # STYLE
    # ============================================================

    def _determine_style(
        self,
        brute_force,
        optimization,
        algorithm_diversity,
        data_structure_diversity,
        recursion_percentage
    ):

        if brute_force >= 65:
            return (
                "Brute-Force Explorer",
                "Frequently relies on nested-loop or "
                "high-complexity approaches."
            )

        if optimization >= 70:
            return (
                "Optimization First",
                "Frequently uses efficient algorithms "
                "and data structures."
            )

        if data_structure_diversity >= 70:
            return (
                "Data Structure Explorer",
                "Uses a broad range of data structures."
            )

        if recursion_percentage >= 30:
            return (
                "Recursive Thinker",
                "Frequently uses recursive problem-solving."
            )

        if algorithm_diversity >= 70:
            return (
                "Algorithm Explorer",
                "Uses a wide range of algorithmic techniques."
            )

        return (
            "Balanced Programmer",
            "Uses a relatively diverse set of "
            "programming techniques."
        )

    # ============================================================
    # STRENGTHS
    # ============================================================

    def _find_strengths(
        self,
        algorithm_diversity,
        data_structure_diversity,
        optimization,
        code_quality,
        improvement,
        recursion_percentage
    ):

        strengths = []

        if code_quality >= 70:
            strengths.append(
                "Good code maintainability"
            )

        if algorithm_diversity >= 70:
            strengths.append(
                "Good algorithmic diversity"
            )

        if data_structure_diversity >= 70:
            strengths.append(
                "Good data-structure diversity"
            )

        if optimization >= 70:
            strengths.append(
                "Strong optimization habits"
            )

        if improvement >= 65:
            strengths.append(
                "Evidence of improvement over time"
            )

        if recursion_percentage >= 20:
            strengths.append(
                "Comfortable with recursion"
            )

        return strengths

    # ============================================================
    # WEAKNESSES
    # ============================================================

    def _find_weaknesses(
        self,
        brute_force,
        optimization,
        algorithm_diversity,
        data_structure_diversity,
        average_complexity,
        pattern_counts
    ):

        weaknesses = []

        if brute_force >= 60:
            weaknesses.append(
                "Tendency toward brute-force solutions"
            )

        if optimization < 45:
            weaknesses.append(
                "Algorithm optimization"
            )

        if algorithm_diversity < 40:
            weaknesses.append(
                "Limited algorithmic diversity"
            )

        if data_structure_diversity < 40:
            weaknesses.append(
                "Limited data-structure diversity"
            )

        if average_complexity >= 6:
            weaknesses.append(
                "High average code complexity"
            )

        if pattern_counts.get(
            "dynamic_programming",
            0
        ) == 0:

            weaknesses.append(
                "Limited dynamic-programming exposure"
            )

        if pattern_counts.get(
            "graph_traversal",
            0
        ) == 0:

            weaknesses.append(
                "Limited graph-algorithm exposure"
            )

        return weaknesses

    # ============================================================
    # RECOMMENDATIONS
    # ============================================================

    def _generate_recommendations(
        self,
        brute_force,
        optimization,
        algorithm_diversity,
        data_structure_diversity,
        average_complexity,
        pattern_counts,
        trend
    ):

        recommendations = []

        if brute_force >= 50:

            recommendations.append(
                "Practice replacing nested loops with "
                "hash maps, two pointers, and "
                "sliding-window techniques."
            )

        if optimization < 50:

            recommendations.append(
                "Analyze time complexity before "
                "implementing a solution."
            )

        if data_structure_diversity < 50:

            recommendations.append(
                "Expand your use of dictionaries, sets, "
                "stacks, queues, and heaps."
            )

        if algorithm_diversity < 50:

            recommendations.append(
                "Practice problems from different "
                "algorithmic categories."
            )

        if average_complexity >= 5:

            recommendations.append(
                "Focus on reducing the complexity "
                "of your solutions."
            )

        if pattern_counts.get(
            "binary_search",
            0
        ) == 0:

            recommendations.append(
                "Practice binary-search problems."
            )

        if pattern_counts.get(
            "dynamic_programming",
            0
        ) == 0:

            recommendations.append(
                "Start with basic dynamic-programming problems."
            )

        if trend.get("available"):

            if trend["complexity_improvement"] < -10:

                recommendations.append(
                    "Your recent solutions are becoming "
                    "more complex. Review recent approaches "
                    "for possible optimization."
                )

            elif trend["complexity_improvement"] > 10:

                recommendations.append(
                    "Your recent solutions show improved "
                    "complexity. Keep building on this."
                )

        if not recommendations:

            recommendations.append(
                "Continue solving a diverse range "
                "of algorithmic problems."
            )

        return recommendations

    # ============================================================
    # JSON PARSER
    # ============================================================

    def _parse_json(
        self,
        submission,
        key,
        default
    ):

        try:

            value = submission[key]

            if not value:
                return default

            if isinstance(value, str):
                return json.loads(value)

            return value

        except (
            KeyError,
            TypeError,
            json.JSONDecodeError
        ):

            return default