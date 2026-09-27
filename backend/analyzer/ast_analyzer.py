"""
ast_analyzer.py
================

Phase 1 of the AI Programmer Behavior Analyzer.

This module is responsible for turning a raw Python source string into a
structured, numeric "feature dictionary" that later stages (complexity
analysis, ML behavior analysis, dashboards) can consume.

Design decisions (documented per project rules):

1. We use Python's built-in `ast` module rather than regex/text parsing.
   Regex-based "parsing" of code is unreliable (breaks on strings/comments
   that look like code, nested brackets, etc). AST parsing gives us a real
   syntax tree to reason about.

2. Every "pattern detection" feature (sorting, binary search, two pointers,
   etc.) is a HEURISTIC, not a guarantee. We attach a confidence score
   (0.0 - 1.0) to each detected pattern instead of a boolean, and we say so
   explicitly in the output. This follows the project rule: "Do not claim
   exact detection is perfect."

3. The analyzer is intentionally a single class (`CodeAnalyzer`) with one
   public method (`analyze`) that returns a plain dict / JSON-serializable
   structure, so it can be dropped into a FastAPI route, a CLI, or a test
   harness without modification.

4. Invalid/unparseable code is handled gracefully -- we never raise an
   uncaught exception out of `analyze()`. Instead we return a dict with
   `"valid": False` and an `"error"` message, so calling code (e.g. an API
   endpoint) can respond sensibly instead of crashing.
"""

from __future__ import annotations

import ast
import io
import tokenize
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Internal helper: a single pass AST visitor that collects raw structural
# facts about the code. Keeping this separate from CodeAnalyzer keeps the
# "walk the tree" concern isolated from the "turn facts into features"
# concern (feature_extractor.py will later build on top of this too).
# ---------------------------------------------------------------------------
class _StructuralVisitor(ast.NodeVisitor):
    """
    Walks the AST once and gathers raw counts / node lists.

    We deliberately avoid doing multiple full tree-walks for each metric
    (e.g. one walk for loops, another for ifs, another for functions) --
    that would be O(k * n) for k metrics. A single visitor pass is O(n).
    """

    def __init__(self) -> None:
        # General
        self.function_defs: List[ast.FunctionDef] = []
        self.async_function_defs: List[ast.AsyncFunctionDef] = []
        self.class_defs: List[ast.ClassDef] = []
        self.imports: List[ast.AST] = []
        self.assignments: List[ast.Assign] = []
        self.ann_assignments: List[ast.AnnAssign] = []

        # Control flow
        self.if_statements: List[ast.If] = []
        self.for_loops: List[ast.For] = []
        self.while_loops: List[ast.While] = []
        self.try_blocks: List[ast.Try] = []
        self.ternary_exprs: List[ast.IfExp] = []
        self.comprehensions: List[ast.AST] = []  # list/set/dict/gen comps

        # Nesting depth tracking for loops specifically
        self.max_loop_nesting_depth: int = 0
        self.nested_loop_count: int = 0  # loops that contain >=1 other loop
        self._current_loop_depth: int = 0

        # Data structure literal usage (raw AST node counts)
        self.list_literals: List[ast.List] = []
        self.tuple_literals: List[ast.Tuple] = []
        self.set_literals: List[ast.Set] = []
        self.dict_literals: List[ast.Dict] = []
        self.string_literals: List[ast.Constant] = []

        # Calls (used heavily for pattern detection later)
        self.calls: List[ast.Call] = []

        # Names read anywhere (used for heuristics like "left"/"right")
        self.name_loads: Set[str] = set()

        # `x in y` / `x not in y` membership comparisons (real AST-level
        # detection, NOT a text substring search -- substring-searching
        # for "in" would false-positive on "print", "return", "int", etc.)
        self.membership_checks: List[ast.Compare] = []

        # Attribute calls like `stack.append(...)` / `stack.pop()` where the
        # receiver is a plain variable name -- used for stack/queue heuristics.
        self.append_pop_calls: List[ast.Call] = []

    # -- Functions -----------------------------------------------------
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_defs.append(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.async_function_defs.append(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_defs.append(node)
        self.generic_visit(node)

    # -- Imports ---------------------------------------------------------
    def visit_Import(self, node: ast.Import) -> None:
        self.imports.append(node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.imports.append(node)
        self.generic_visit(node)

    # -- Assignments -------------------------------------------------------
    def visit_Assign(self, node: ast.Assign) -> None:
        self.assignments.append(node)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.ann_assignments.append(node)
        self.generic_visit(node)

    # -- Control flow --------------------------------------------------
    def visit_If(self, node: ast.If) -> None:
        self.if_statements.append(node)
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self.ternary_exprs.append(node)
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        self.try_blocks.append(node)
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self.comprehensions.append(node)
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self.comprehensions.append(node)
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self.comprehensions.append(node)
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self.comprehensions.append(node)
        self.generic_visit(node)

    # -- Loops (with nesting-depth tracking) ----------------------------
    def _visit_loop(self, node) -> None:
        self._current_loop_depth += 1
        if self._current_loop_depth > self.max_loop_nesting_depth:
            self.max_loop_nesting_depth = self._current_loop_depth
        if self._current_loop_depth >= 2:
            self.nested_loop_count += 1
        self.generic_visit(node)
        self._current_loop_depth -= 1

    def visit_For(self, node: ast.For) -> None:
        self.for_loops.append(node)
        self._visit_loop(node)

    def visit_While(self, node: ast.While) -> None:
        self.while_loops.append(node)
        self._visit_loop(node)

    # -- Data structure literals -----------------------------------------
    def visit_List(self, node: ast.List) -> None:
        self.list_literals.append(node)
        self.generic_visit(node)

    def visit_Tuple(self, node: ast.Tuple) -> None:
        self.tuple_literals.append(node)
        self.generic_visit(node)

    def visit_Set(self, node: ast.Set) -> None:
        self.set_literals.append(node)
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> None:
        self.dict_literals.append(node)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str):
            self.string_literals.append(node)
        self.generic_visit(node)

    # -- Calls / Names -----------------------------------------------------
    def visit_Call(self, node: ast.Call) -> None:
        self.calls.append(node)
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and func.attr in ("append", "pop")
            and isinstance(func.value, ast.Name)
        ):
            self.append_pop_calls.append(node)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.name_loads.add(node.id)
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        if any(isinstance(op, (ast.In, ast.NotIn)) for op in node.ops):
            self.membership_checks.append(node)
        self.generic_visit(node)


@dataclass
class PatternMatch:
    """A single detected algorithmic pattern with a confidence score."""
    name: str
    confidence: float  # 0.0 - 1.0
    evidence: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern": self.name,
            "confidence": round(self.confidence, 2),
            "evidence": self.evidence,
        }


class CodeAnalyzer:
    """
    Public entry point for Phase 1.

    Usage:
        analyzer = CodeAnalyzer()
        features = analyzer.analyze(source_code)
    """

    # Function-call names we treat as "sorting" for heuristic purposes.
    _SORT_CALL_NAMES = {"sorted"}
    _SORT_METHOD_NAMES = {"sort"}

    # Modules whose import signals a specific technique.
    _BINARY_SEARCH_MODULES = {"bisect"}
    _DP_MEMO_MODULES = {"functools"}  # lru_cache / cache
    _GRAPH_MODULES = {"collections"}  # deque used for BFS, heapq for graphs/heaps
    _HEAP_MODULES = {"heapq"}
    _QUEUE_MODULES = {"queue", "collections"}

    def analyze(self, code: str) -> Dict[str, Any]:
        """
        Parse `code` and return a structured feature dictionary.

        Returns a dict that always contains at least the key "valid".
        If parsing fails, only "valid" and "error" are guaranteed --
        callers must check `valid` before reading other keys.
        """
        if not isinstance(code, str) or code.strip() == "":
            return {
                "valid": False,
                "error": "Empty or non-string input provided.",
            }

        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            return {
                "valid": False,
                "error": f"SyntaxError: {exc.msg} (line {exc.lineno}, col {exc.offset})",
            }
        except (ValueError, TypeError) as exc:
            # ast.parse can raise ValueError on null bytes etc.
            return {
                "valid": False,
                "error": f"Could not parse source: {exc}",
            }

        visitor = _StructuralVisitor()
        visitor.visit(tree)

        loc_features = self._analyze_loc_and_comments(code)
        function_features = self._analyze_functions(visitor)
        data_structure_features = self._analyze_data_structures(visitor, code)
        has_slicing = _tree_has_slicing(tree)
        pattern_matches = self._detect_patterns(visitor, code, function_features, has_slicing)

        features: Dict[str, Any] = {
            "valid": True,
            "error": None,

            # ---- General ----
            "loc": loc_features["loc"],
            "blank_lines": loc_features["blank_lines"],
            "comment_lines": loc_features["comment_lines"],
            "num_functions": len(visitor.function_defs) + len(visitor.async_function_defs),
            "num_classes": len(visitor.class_defs),
            "num_imports": len(visitor.imports),
            "num_variables": self._count_variables(visitor),
            "num_constants": self._count_constants(visitor),

            # ---- Control flow ----
            "if_statements": len(visitor.if_statements),
            "for_loops": len(visitor.for_loops),
            "while_loops": len(visitor.while_loops),
            "total_loops": len(visitor.for_loops) + len(visitor.while_loops),
            "nested_loops": visitor.nested_loop_count,
            "max_loop_nesting_depth": visitor.max_loop_nesting_depth,
            "try_except_blocks": len(visitor.try_blocks),
            "conditional_expressions": len(visitor.ternary_exprs),
            "comprehensions": len(visitor.comprehensions),

            # ---- Functions ----
            "avg_function_length": function_features["avg_function_length"],
            "max_function_length": function_features["max_function_length"],
            "avg_function_args": function_features["avg_function_args"],
            "total_return_statements": function_features["total_return_statements"],
            "recursive_functions": function_features["recursive_functions"],
            "recursive_function_names": function_features["recursive_function_names"],

            # ---- Data structures ----
            "data_structures": data_structure_features,

            # ---- Patterns (heuristic, confidence-scored) ----
            "patterns": [p.to_dict() for p in pattern_matches],
        }

        return features

    # ------------------------------------------------------------------
    # LOC / comments -- uses `tokenize` rather than naive `startswith('#')`
    # so that comments and multi-line strings are handled correctly.
    # ------------------------------------------------------------------
    def _analyze_loc_and_comments(self, code: str) -> Dict[str, int]:
        lines = code.splitlines()
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if line.strip() == "")

        comment_lines = 0
        try:
            tokens = tokenize.generate_tokens(io.StringIO(code).readline)
            comment_line_numbers: Set[int] = set()
            for tok in tokens:
                if tok.type == tokenize.COMMENT:
                    comment_line_numbers.add(tok.start[0])
            comment_lines = len(comment_line_numbers)
        except (tokenize.TokenizeError, IndentationError, SyntaxError):
            # Fall back to a naive count if tokenize chokes (rare, e.g.
            # mixed tabs/spaces that ast.parse tolerated differently).
            comment_lines = sum(
                1 for line in lines if line.strip().startswith("#")
            )

        loc = total_lines - blank_lines - comment_lines
        return {
            "loc": max(loc, 0),
            "blank_lines": blank_lines,
            "comment_lines": comment_lines,
        }

    # ------------------------------------------------------------------
    def _count_variables(self, visitor: _StructuralVisitor) -> int:
        """
        Approximate variable count: distinct names that appear as an
        assignment target. This is an approximation -- Python has no
        static variable declarations, so "number of variables" is
        inherently a heuristic (we count distinct bound names).
        """
        names: Set[str] = set()
        for assign in visitor.assignments:
            for target in assign.targets:
                self._collect_name_targets(target, names)
        for ann in visitor.ann_assignments:
            self._collect_name_targets(ann.target, names)
        return len(names)

    def _collect_name_targets(self, target: ast.AST, names: Set[str]) -> None:
        if isinstance(target, ast.Name):
            names.add(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                self._collect_name_targets(elt, names)
        # Attribute/Subscript targets (e.g. self.x = 1, arr[0] = 1) are
        # deliberately not counted as new "variables".

    def _count_constants(self, visitor: _StructuralVisitor) -> int:
        """
        Heuristic: assignments to ALL_CAPS names are treated as constants,
        matching common Python convention (there's no `const` keyword).
        """
        count = 0
        for assign in visitor.assignments:
            for target in assign.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    count += 1
        return count

    # ------------------------------------------------------------------
    def _analyze_functions(self, visitor: _StructuralVisitor) -> Dict[str, Any]:
        all_funcs: List[Any] = list(visitor.function_defs) + list(visitor.async_function_defs)

        if not all_funcs:
            return {
                "avg_function_length": 0,
                "max_function_length": 0,
                "avg_function_args": 0,
                "total_return_statements": 0,
                "recursive_functions": 0,
                "recursive_function_names": [],
            }

        lengths: List[int] = []
        arg_counts: List[int] = []
        total_returns = 0
        recursive_names: List[str] = []

        for func in all_funcs:
            start = func.lineno
            end = getattr(func, "end_lineno", start)
            lengths.append(max(end - start + 1, 1))

            args = func.args
            n_args = (
                len(args.args)
                + len(args.posonlyargs)
                + len(args.kwonlyargs)
                + (1 if args.vararg else 0)
                + (1 if args.kwarg else 0)
            )
            arg_counts.append(n_args)

            returns_in_func = sum(1 for n in ast.walk(func) if isinstance(n, ast.Return))
            total_returns += returns_in_func

            if self._is_recursive(func):
                recursive_names.append(func.name)

        return {
            "avg_function_length": round(sum(lengths) / len(lengths), 2),
            "max_function_length": max(lengths),
            "avg_function_args": round(sum(arg_counts) / len(arg_counts), 2),
            "total_return_statements": total_returns,
            "recursive_functions": len(recursive_names),
            "recursive_function_names": recursive_names,
        }

    def _is_recursive(self, func_node) -> bool:
        """
        Direct-recursion detection: does the function body contain a call
        whose callee name matches the function's own name?

        Note: this only detects DIRECT recursion (f calls f). Mutual
        recursion (f calls g calls f) is NOT detected in this version --
        documenting that as a known limitation rather than silently
        under-reporting with false confidence.
        """
        func_name = func_node.name
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                callee = node.func
                if isinstance(callee, ast.Name) and callee.id == func_name:
                    return True
        return False

    # ------------------------------------------------------------------
    def _analyze_data_structures(
        self, visitor: _StructuralVisitor, code: str
    ) -> Dict[str, Any]:
        imported_modules = self._imported_module_names(visitor)

        # Stacks/queues/heaps are not real Python types, so detection is
        # necessarily heuristic: we look for the idiomatic APIs used to
        # implement them (`.append()`/`.pop()` on a variable), NOT merely
        # the presence of a list literal -- most list literals are just
        # data, not a stack being pushed/popped.
        uses_list_as_stack = len(visitor.append_pop_calls) > 0

        uses_deque = "deque" in self._imported_names(visitor)
        uses_heapq = bool(imported_modules & self._HEAP_MODULES)
        uses_queue_module = "queue" in imported_modules

        return {
            "list_usage": len(visitor.list_literals),
            "tuple_usage": len(visitor.tuple_literals),
            "set_usage": len(visitor.set_literals),
            "dict_usage": len(visitor.dict_literals),
            "string_literal_usage": len(visitor.string_literals),
            "stack_detected": uses_deque or uses_list_as_stack,
            "queue_detected": uses_deque or uses_queue_module,
            "heap_detected": uses_heapq,
        }

    def _imported_module_names(self, visitor: _StructuralVisitor) -> Set[str]:
        modules: Set[str] = set()
        for imp in visitor.imports:
            if isinstance(imp, ast.Import):
                for alias in imp.names:
                    modules.add(alias.name.split(".")[0])
            elif isinstance(imp, ast.ImportFrom) and imp.module:
                modules.add(imp.module.split(".")[0])
        return modules

    def _imported_names(self, visitor: _StructuralVisitor) -> Set[str]:
        names: Set[str] = set()
        for imp in visitor.imports:
            if isinstance(imp, ast.Import):
                for alias in imp.names:
                    names.add((alias.asname or alias.name).split(".")[0])
            elif isinstance(imp, ast.ImportFrom):
                for alias in imp.names:
                    names.add(alias.asname or alias.name)
        return names

    # ------------------------------------------------------------------
    # Pattern detection -- ALL heuristic, ALL confidence-scored.
    # We are explicit in comments about *why* each heuristic is imperfect.
    # ------------------------------------------------------------------
    def _detect_patterns(
        self,
        visitor: _StructuralVisitor,
        code: str,
        function_features: Dict[str, Any],
        has_slicing: bool = False,
    ) -> List[PatternMatch]:
        matches: List[PatternMatch] = []
        imported_modules = self._imported_module_names(visitor)
        imported_names = self._imported_names(visitor)
        call_names = self._call_names(visitor)

        # --- Sorting ---------------------------------------------------
        if call_names & self._SORT_CALL_NAMES or self._has_sort_method_call(visitor):
            matches.append(PatternMatch(
                "sorting", 0.9,
                "Found call to sorted() or .sort()."
            ))

        # --- Binary search ----------------------------------------------
        bs_conf = 0.0
        evidence_bits = []
        if "bisect" in imported_modules:
            bs_conf += 0.6
            evidence_bits.append("imports bisect")
        if "mid" in visitor.name_loads and ("low" in visitor.name_loads or "left" in visitor.name_loads) and (
            "high" in visitor.name_loads or "right" in visitor.name_loads
        ):
            bs_conf += 0.4
            evidence_bits.append("uses low/high/mid-style variable names")
        if bs_conf > 0:
            matches.append(PatternMatch(
                "binary_search", min(bs_conf, 1.0), "; ".join(evidence_bits)
            ))

        # --- Two pointers -------------------------------------------------
        two_pointer_names = {"left", "right"} <= visitor.name_loads or \
            ({"i", "j"} <= visitor.name_loads and visitor.while_loops)
        if two_pointer_names:
            matches.append(PatternMatch(
                "two_pointers", 0.55,
                "Found left/right or i/j pointer-style variable names in a loop."
            ))

        # --- Sliding window -----------------------------------------------
        window_names = {"window", "start", "end"} & visitor.name_loads
        if len(window_names) >= 2:
            matches.append(PatternMatch(
                "sliding_window", 0.5,
                f"Found window-style variable names: {sorted(window_names)}."
            ))

        # --- Recursion ------------------------------------------------------
        if function_features["recursive_functions"] > 0:
            matches.append(PatternMatch(
                "recursion", 1.0,
                f"Function(s) call themselves directly: "
                f"{function_features['recursive_function_names']}."
            ))

            # --- Divide and conquer (recursion + slicing/halving) ---------
            if has_slicing or "mid" in visitor.name_loads:
                matches.append(PatternMatch(
                    "divide_and_conquer", 0.6,
                    "Recursive function combined with slicing or a midpoint "
                    "variable (typical of merge sort / quick sort style code)."
                ))

        # --- Brute force ----------------------------------------------------
        # Heuristic: nested loops present AND no advanced structure
        # (hash map / set / sorted / binary search) used to cut the work down.
        has_optimization_signal = bool(
            visitor.dict_literals or visitor.set_literals or
            (call_names & self._SORT_CALL_NAMES) or bs_conf > 0
        )
        if visitor.nested_loop_count > 0 and not has_optimization_signal:
            matches.append(PatternMatch(
                "brute_force", 0.7,
                "Nested loops present with no hash map, set, sort, or "
                "binary search detected to reduce the work."
            ))

        # --- Hash-map lookup --------------------------------------------
        if visitor.dict_literals and (visitor.for_loops or visitor.while_loops):
            matches.append(PatternMatch(
                "hash_map_lookup", 0.65,
                "Dictionary literal(s) used alongside a loop."
            ))

        # --- Dynamic programming indicators --------------------------------
        dp_conf = 0.0
        dp_evidence = []
        if "lru_cache" in imported_names or "cache" in imported_names:
            dp_conf += 0.6
            dp_evidence.append("uses functools.lru_cache/cache")
        if any(n in visitor.name_loads for n in ("memo", "dp", "cache")):
            dp_conf += 0.4
            dp_evidence.append("uses memo/dp/cache-named variable")
        if dp_conf > 0:
            matches.append(PatternMatch(
                "dynamic_programming", min(dp_conf, 1.0), "; ".join(dp_evidence)
            ))

        # --- Greedy indicators -------------------------------------------
        if (call_names & self._SORT_CALL_NAMES or self._has_sort_method_call(visitor)) \
                and (visitor.for_loops or visitor.while_loops) \
                and function_features["recursive_functions"] == 0:
            matches.append(PatternMatch(
                "greedy", 0.35,
                "Sorting followed by a single-pass loop (weak signal; "
                "greedy intent cannot be confirmed from structure alone)."
            ))

        # --- Graph traversal indicators -------------------------------------
        graph_conf = 0.0
        graph_evidence = []
        if {"visited", "graph", "adj", "adjacency"} & visitor.name_loads:
            graph_conf += 0.4
            graph_evidence.append("uses visited/graph/adjacency-named variable")
        if "deque" in imported_names:
            graph_conf += 0.3
            graph_evidence.append("imports collections.deque (common in BFS)")
        if "heapq" in imported_modules:
            graph_conf += 0.2
            graph_evidence.append("imports heapq (common in Dijkstra/graph algorithms)")
        if graph_conf > 0:
            matches.append(PatternMatch(
                "graph_traversal", min(graph_conf, 1.0), "; ".join(graph_evidence)
            ))

        # --- Searching (generic, non-binary) --------------------------------
        # Real AST-level detection of `x in y` / `x not in y` comparisons
        # (NOT a text substring search on the source -- a substring search
        # for "in" would false-positive on words like "print" or "return").
        if visitor.membership_checks and (visitor.for_loops or visitor.while_loops) and bs_conf == 0:
            matches.append(PatternMatch(
                "linear_search", 0.3,
                f"Found {len(visitor.membership_checks)} membership check(s) "
                f"(`in` / `not in`) inside a loop; weak signal since membership "
                f"tests are used for many purposes beyond searching."
            ))

        return matches

    def _call_names(self, visitor: _StructuralVisitor) -> Set[str]:
        names: Set[str] = set()
        for call in visitor.calls:
            func = call.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
        return names

    def _has_sort_method_call(self, visitor: _StructuralVisitor) -> bool:
        for call in visitor.calls:
            func = call.func
            if isinstance(func, ast.Attribute) and func.attr in self._SORT_METHOD_NAMES:
                return True
        return False


# ---------------------------------------------------------------------------
# Detecting slice expressions (e.g. `arr[:mid]`) requires walking the tree
# for ast.Subscript nodes whose `.slice` is an ast.Slice. This is a cheap,
# separate O(n) walk run once per analyze() call, only used as a weak signal
# for divide-and-conquer pattern detection.
# ---------------------------------------------------------------------------
def _tree_has_slicing(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and isinstance(getattr(node, "slice", None), ast.Slice):
            return True
    return False
