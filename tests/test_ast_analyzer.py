"""
test_ast_analyzer.py

Hard-assertion regression tests for Phase 1 (CodeAnalyzer).

Run with:
    pytest tests/test_ast_analyzer.py -v

These complement run_ast_analyzer_tests.py (which is for human eyeballing)
by pinning down exact expected values so future refactors of the analyzer
don't silently change behavior.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from analyzer.ast_analyzer import CodeAnalyzer  # noqa: E402


def make_analyzer():
    return CodeAnalyzer()


# ---------------------------------------------------------------------------
# Basic validity / error handling
# ---------------------------------------------------------------------------
def test_empty_input_is_invalid():
    analyzer = make_analyzer()
    result = analyzer.analyze("")
    assert result["valid"] is False
    assert "error" in result


def test_whitespace_only_input_is_invalid():
    analyzer = make_analyzer()
    result = analyzer.analyze("   \n\n   ")
    assert result["valid"] is False


def test_invalid_syntax_does_not_raise():
    analyzer = make_analyzer()
    broken_code = "def f(x, y)\n    return x + y"
    result = analyzer.analyze(broken_code)
    assert result["valid"] is False
    assert "SyntaxError" in result["error"]


def test_non_string_input_does_not_raise():
    analyzer = make_analyzer()
    result = analyzer.analyze(None)  # type: ignore[arg-type]
    assert result["valid"] is False


# ---------------------------------------------------------------------------
# Structural counts
# ---------------------------------------------------------------------------
def test_function_and_class_counts():
    code = """
class A:
    def method_one(self):
        pass

    def method_two(self):
        pass

def standalone():
    pass
"""
    result = make_analyzer().analyze(code)
    assert result["valid"] is True
    assert result["num_classes"] == 1
    assert result["num_functions"] == 3


def test_nested_loop_detection():
    code = """
def f(matrix):
    for row in matrix:
        for cell in row:
            print(cell)
"""
    result = make_analyzer().analyze(code)
    assert result["for_loops"] == 2
    assert result["nested_loops"] == 1
    assert result["max_loop_nesting_depth"] == 2


def test_triple_nested_loop_depth():
    code = """
def f(cube):
    for x in cube:
        for y in x:
            for z in y:
                print(z)
"""
    result = make_analyzer().analyze(code)
    assert result["max_loop_nesting_depth"] == 3
    assert result["nested_loops"] == 2  # the 2nd and 3rd loops are "nested"


def test_no_loops_means_no_nesting():
    code = "def f():\n    return 1\n"
    result = make_analyzer().analyze(code)
    assert result["total_loops"] == 0
    assert result["nested_loops"] == 0
    assert result["max_loop_nesting_depth"] == 0


# ---------------------------------------------------------------------------
# Recursion detection
# ---------------------------------------------------------------------------
def test_direct_recursion_detected():
    code = """
def fact(n):
    if n <= 1:
        return 1
    return n * fact(n - 1)
"""
    result = make_analyzer().analyze(code)
    assert result["recursive_functions"] == 1
    assert result["recursive_function_names"] == ["fact"]


def test_non_recursive_function_not_flagged():
    code = """
def add(a, b):
    return a + b
"""
    result = make_analyzer().analyze(code)
    assert result["recursive_functions"] == 0


def test_mutual_recursion_not_detected_documented_limitation():
    """
    Known limitation: this analyzer only detects DIRECT recursion
    (f calls f). Mutual recursion (f calls g, g calls f) is not detected.
    This test documents/pins that limitation rather than hiding it.
    """
    code = """
def is_even(n):
    if n == 0:
        return True
    return is_odd(n - 1)

def is_odd(n):
    if n == 0:
        return False
    return is_even(n - 1)
"""
    result = make_analyzer().analyze(code)
    assert result["recursive_functions"] == 0


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
def test_dict_and_list_usage_counts():
    code = """
def f():
    d = {"a": 1}
    lst = [1, 2, 3]
    return d, lst
"""
    result = make_analyzer().analyze(code)
    assert result["data_structures"]["dict_usage"] == 1
    assert result["data_structures"]["list_usage"] == 1


def test_stack_detection_requires_append_pop_not_just_a_list():
    code_without_push_pop = "def f():\n    x = [1, 2, 3]\n    return x\n"
    code_with_push_pop = "def f():\n    stack = []\n    stack.append(1)\n    stack.pop()\n    return stack\n"

    result_without = make_analyzer().analyze(code_without_push_pop)
    result_with = make_analyzer().analyze(code_with_push_pop)

    assert result_without["data_structures"]["stack_detected"] is False
    assert result_with["data_structures"]["stack_detected"] is True


def test_deque_import_flags_queue():
    code = "from collections import deque\nq = deque()\n"
    result = make_analyzer().analyze(code)
    assert result["data_structures"]["queue_detected"] is True


# ---------------------------------------------------------------------------
# Pattern detection (heuristic; check presence + reasonable confidence)
# ---------------------------------------------------------------------------
def _pattern_names(result):
    return {p["pattern"] for p in result["patterns"]}


def test_sorting_detected():
    code = "def f(x):\n    return sorted(x)\n"
    result = make_analyzer().analyze(code)
    assert "sorting" in _pattern_names(result)


def test_recursion_pattern_has_full_confidence():
    code = "def f(n):\n    if n == 0:\n        return 0\n    return f(n - 1)\n"
    result = make_analyzer().analyze(code)
    patterns = {p["pattern"]: p["confidence"] for p in result["patterns"]}
    assert patterns.get("recursion") == 1.0


def test_brute_force_flagged_for_naive_nested_loop_without_optimization():
    code = """
def f(a, b):
    result = []
    for x in a:
        for y in b:
            if x == y:
                result.append(x)
    return result
"""
    result = make_analyzer().analyze(code)
    assert "brute_force" in _pattern_names(result)


def test_brute_force_not_flagged_when_hash_map_used():
    code = """
def f(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return True
        seen[n] = i
    return False
"""
    result = make_analyzer().analyze(code)
    assert "brute_force" not in _pattern_names(result)


def test_all_patterns_have_confidence_in_valid_range():
    code = """
from collections import deque

def bfs(graph, start):
    visited = {start}
    queue = deque([start])
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for nb in graph.get(node, []):
            if nb not in visited:
                visited.add(nb)
                queue.append(nb)
    return order
"""
    result = make_analyzer().analyze(code)
    for p in result["patterns"]:
        assert 0.0 <= p["confidence"] <= 1.0


# ---------------------------------------------------------------------------
# LOC / comments (tokenize-based, not naive string matching)
# ---------------------------------------------------------------------------
def test_loc_excludes_blank_and_comment_lines():
    code = "# a comment\n\ndef f():\n    return 1\n"
    result = make_analyzer().analyze(code)
    assert result["comment_lines"] == 1
    assert result["blank_lines"] == 1
    assert result["loc"] == 2  # def line + return line


def test_comment_inside_string_is_not_counted_as_comment():
    code = 'def f():\n    return "# not a comment"\n'
    result = make_analyzer().analyze(code)
    assert result["comment_lines"] == 0


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
