from __future__ import annotations

import io
from typing import Any, Dict

from radon.complexity import cc_visit
from radon.metrics import mi_visit
from radon.raw import analyze


class ComplexityAnalyzer:
    """
    Phase 2 of the AI Programmer Behavior Analyzer.

    Uses Radon to calculate:
    - Lines of code
    - Logical lines of code
    - Source lines of code
    - Comments
    - Cyclomatic complexity
    - Maintainability index
    """

    def analyze(self, code: str) -> Dict[str, Any]:
        """
        Analyze Python source code and return complexity metrics.

        Returns:
            Dictionary containing Radon metrics.
        """

        if not isinstance(code, str) or not code.strip():
            return {
                "valid": False,
                "error": "Empty or non-string input provided."
            }

        try:
            # ---------------------------------------------------------
            # Raw source metrics
            # ---------------------------------------------------------
            raw = analyze(code)

            # ---------------------------------------------------------
            # Cyclomatic complexity
            # ---------------------------------------------------------
            complexity_blocks = cc_visit(code)

            complexities = []

            for block in complexity_blocks:
                complexities.append({
                    "name": block.name,
                    "type": block.classname,
                    "complexity": block.complexity,
                    "line": block.lineno,
                    "end_line": block.endline,
                })

            # ---------------------------------------------------------
            # Maintainability Index
            # ---------------------------------------------------------
            maintainability_index = mi_visit(code, multi=True)

            # ---------------------------------------------------------
            # Average / maximum complexity
            # ---------------------------------------------------------
            if complexities:
                complexity_values = [
                    item["complexity"]
                    for item in complexities
                ]

                average_complexity = round(
                    sum(complexity_values) / len(complexity_values),
                    2
                )

                maximum_complexity = max(complexity_values)

            else:
                average_complexity = 0
                maximum_complexity = 0

            return {
                "valid": True,
                "error": None,

                "raw_metrics": {
                    "loc": raw.loc,
                    "lloc": raw.lloc,
                    "sloc": raw.sloc,
                    "comments": raw.comments,
                    "multi": raw.multi,
                    "blank": raw.blank,
                },

                "cyclomatic_complexity": {
                    "average": average_complexity,
                    "maximum": maximum_complexity,
                    "blocks": complexities,
                },

                "maintainability_index": round(
                    maintainability_index,
                    2
                ),
            }

        except SyntaxError as exc:
            return {
                "valid": False,
                "error": (
                    f"SyntaxError: {exc.msg} "
                    f"(line {exc.lineno}, col {exc.offset})"
                ),
            }

        except Exception as exc:
            return {
                "valid": False,
                "error": f"Complexity analysis failed: {exc}",
            }