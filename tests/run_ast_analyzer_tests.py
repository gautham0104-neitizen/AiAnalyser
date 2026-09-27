"""
run_ast_analyzer_tests.py

Phase 1 verification script.

Loads every .py file in tests/sample_programs/, runs it through
CodeAnalyzer.analyze(), and pretty-prints the resulting feature dict.

This is a manual/inspection test runner (not pytest) so a human can eyeball
whether the extracted features "look right" for each style of program
before we trust the feature extraction enough to build ML on top of it.
A pytest-based regression suite (tests/test_ast_analyzer.py) is added
separately with hard assertions.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from analyzer.ast_analyzer import CodeAnalyzer  # noqa: E402


SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_programs")


def main() -> None:
    analyzer = CodeAnalyzer()
    sample_files = sorted(f for f in os.listdir(SAMPLE_DIR) if f.endswith(".py"))

    if not sample_files:
        print("No sample programs found in", SAMPLE_DIR)
        return

    for filename in sample_files:
        path = os.path.join(SAMPLE_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()

        features = analyzer.analyze(code)

        print("=" * 80)
        print(f"FILE: {filename}")
        print("=" * 80)

        if not features["valid"]:
            print(f"  INVALID CODE -> {features['error']}")
            print()
            continue

        # Print top-level scalar features compactly.
        scalar_keys = [
            "loc", "blank_lines", "comment_lines", "num_functions",
            "num_classes", "num_imports", "num_variables", "num_constants",
            "if_statements", "for_loops", "while_loops", "total_loops",
            "nested_loops", "max_loop_nesting_depth", "try_except_blocks",
            "conditional_expressions", "comprehensions",
            "avg_function_length", "max_function_length", "avg_function_args",
            "total_return_statements", "recursive_functions",
        ]
        for key in scalar_keys:
            print(f"  {key:28s}: {features[key]}")

        print(f"  {'recursive_function_names':28s}: {features['recursive_function_names']}")
        print(f"  {'data_structures':28s}: {json.dumps(features['data_structures'])}")

        print("  detected_patterns:")
        if features["patterns"]:
            for p in features["patterns"]:
                print(
                    f"    - {p['pattern']:20s} "
                    f"confidence={p['confidence']:.2f}  evidence: {p['evidence']}"
                )
        else:
            print("    (none detected)")
        print()


if __name__ == "__main__":
    main()
