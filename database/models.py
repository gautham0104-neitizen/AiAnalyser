from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: Optional[int]
    username: str


@dataclass
class Submission:
    id: Optional[int]
    user_id: int
    problem_name: str
    language: str
    code: str
    submitted_at: str


@dataclass
class CodeFeatures:
    submission_id: int

    loc: int
    blank_lines: int
    comment_lines: int

    num_functions: int
    num_classes: int
    num_imports: int
    num_variables: int
    num_constants: int

    if_statements: int
    for_loops: int
    while_loops: int
    total_loops: int
    nested_loops: int
    max_loop_nesting_depth: int

    try_except_blocks: int
    conditional_expressions: int
    comprehensions: int

    avg_function_length: float
    max_function_length: int
    avg_function_args: float
    total_return_statements: int

    recursive_functions: int

    cyclomatic_complexity: float
    maximum_cyclomatic_complexity: int
    maintainability_index: float