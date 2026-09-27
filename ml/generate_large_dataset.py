from __future__ import annotations

import sys
from pathlib import Path
import random

# ---------------------------------------------------------
# PROJECT ROOT
# ---------------------------------------------------------

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent)
)

from backend.analyzer.ast_analyzer import CodeAnalyzer
from backend.analyzer.complexity import ComplexityAnalyzer
from backend.analyzer.behavior import BehaviorAnalyzer
from backend.database.database import Database

from ml.feature_builder import MLFeatureBuilder


# =========================================================
# CONFIGURATION
# =========================================================

DB_PATH = "data/ml_dataset_v2.db"

NUMBER_OF_PROGRAMMERS = 30
SUBMISSIONS_PER_PROGRAMMER = 10

random.seed(42)


# =========================================================
# CODE LIBRARY
# =========================================================
#
# Each item represents a REAL Python program.
#
# The ML system will NEVER receive these categories.
# They are only used here to generate varied histories.
# =========================================================

CODE_LIBRARY = {

    "brute_force": [

        (
            "Pair Search",
            """
def find_pair(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]

    return []
"""
        ),

        (
            "Common Elements",
            """
def common(a, b):
    result = []

    for x in a:
        for y in b:
            if x == y:
                result.append(x)

    return result
"""
        ),

        (
            "Duplicate Search",
            """
def duplicate(nums):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] == nums[j]:
                return True

    return False
"""
        ),

        (
            "Maximum Pair",
            """
def max_pair(nums):
    best = 0

    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):

            value = nums[i] * nums[j]

            if value > best:
                best = value

    return best
"""
        )
    ],

    # -----------------------------------------------------

    "hashing": [

        (
            "Frequency Counter",
            """
def frequency(nums):
    counts = {}

    for value in nums:
        counts[value] = counts.get(value, 0) + 1

    return counts
"""
        ),

        (
            "Two Sum",
            """
def two_sum(nums, target):
    seen = {}

    for i, value in enumerate(nums):

        needed = target - value

        if needed in seen:
            return [seen[needed], i]

        seen[value] = i

    return []
"""
        ),

        (
            "First Unique",
            """
def first_unique(nums):
    counts = {}

    for value in nums:
        counts[value] = counts.get(value, 0) + 1

    for value in nums:
        if counts[value] == 1:
            return value

    return None
"""
        )
    ],

    # -----------------------------------------------------

    "binary_search": [

        (
            "Binary Search",
            """
def search(nums, target):

    left = 0
    right = len(nums) - 1

    while left <= right:

        mid = (left + right) // 2

        if nums[mid] == target:
            return mid

        if nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1

    return -1
"""
        ),

        (
            "Search Insert",
            """
def search_insert(nums, target):

    left = 0
    right = len(nums)

    while left < right:

        mid = (left + right) // 2

        if nums[mid] < target:
            left = mid + 1
        else:
            right = mid

    return left
"""
        )
    ],

    # -----------------------------------------------------

    "two_pointer": [

        (
            "Two Pointer",
            """
def pair_sum(nums, target):

    left = 0
    right = len(nums) - 1

    while left < right:

        total = nums[left] + nums[right]

        if total == target:
            return [left, right]

        if total < target:
            left += 1
        else:
            right -= 1

    return []
"""
        ),

        (
            "Remove Duplicates",
            """
def remove_duplicates(nums):

    if not nums:
        return 0

    write = 1

    for read in range(1, len(nums)):

        if nums[read] != nums[read - 1]:
            nums[write] = nums[read]
            write += 1

    return write
"""
        )
    ],

    # -----------------------------------------------------

    "sliding_window": [

        (
            "Maximum Window",
            """
def max_sum(nums, k):

    if k > len(nums):
        return 0

    current = sum(nums[:k])
    best = current

    for i in range(k, len(nums)):

        current += nums[i]
        current -= nums[i - k]

        best = max(best, current)

    return best
"""
        ),

        (
            "Longest Unique",
            """
def longest_unique(text):

    seen = set()
    left = 0
    best = 0

    for right in range(len(text)):

        while text[right] in seen:
            seen.remove(text[left])
            left += 1

        seen.add(text[right])

        best = max(
            best,
            right - left + 1
        )

    return best
"""
        )
    ],

    # -----------------------------------------------------

    "recursion": [

        (
            "Factorial",
            """
def factorial(n):

    if n <= 1:
        return 1

    return n * factorial(n - 1)
"""
        ),

        (
            "Fibonacci",
            """
def fibonacci(n):

    if n <= 1:
        return n

    return (
        fibonacci(n - 1)
        + fibonacci(n - 2)
    )
"""
        ),

        (
            "Power",
            """
def power(x, n):

    if n == 0:
        return 1

    return x * power(x, n - 1)
"""
        ),

        (
            "Tree Depth",
            """
def depth(node):

    if node is None:
        return 0

    left = depth(node.left)
    right = depth(node.right)

    return 1 + max(left, right)
"""
        )
    ],

    # -----------------------------------------------------

    "graph": [

        (
            "Graph BFS",
            """
from collections import deque

def bfs(graph, start):

    visited = {start}
    queue = deque([start])

    while queue:

        node = queue.popleft()

        for neighbor in graph.get(node, []):

            if neighbor not in visited:

                visited.add(neighbor)
                queue.append(neighbor)

    return visited
"""
        ),

        (
            "Graph DFS",
            """
def dfs(graph, start):

    visited = set()

    def visit(node):

        if node in visited:
            return

        visited.add(node)

        for neighbor in graph.get(node, []):
            visit(neighbor)

    visit(start)

    return visited
"""
        )
    ],

    # -----------------------------------------------------

    "dynamic_programming": [

        (
            "Climbing Stairs",
            """
def climb(n):

    if n <= 2:
        return n

    first = 1
    second = 2

    for _ in range(3, n + 1):

        first, second = (
            second,
            first + second
        )

    return second
"""
        ),

        (
            "House Robber",
            """
def rob(nums):

    previous = 0
    current = 0

    for value in nums:

        previous, current = (
            current,
            max(
                current,
                previous + value
            )
        )

    return current
"""
        )
    ],

    # -----------------------------------------------------

    "data_structures": [

        (
            "Stack",
            """
def reverse_text(text):

    stack = []

    for char in text:
        stack.append(char)

    result = []

    while stack:
        result.append(stack.pop())

    return "".join(result)
"""
        ),

        (
            "Queue",
            """
from collections import deque

def process(items):

    queue = deque(items)
    result = []

    while queue:

        value = queue.popleft()
        result.append(value)

    return result
"""
        ),

        (
            "Set Usage",
            """
def unique_values(nums):

    seen = set()

    for value in nums:
        seen.add(value)

    return list(seen)
"""
        )
    ],

    # -----------------------------------------------------

    "sorting": [

        (
            "Sorting",
            """
def sort_values(nums):

    values = nums.copy()

    values.sort()

    return values
"""
        ),

        (
            "Sort By Length",
            """
def sort_words(words):

    return sorted(
        words,
        key=len
    )
"""
        )
    ]
}


# =========================================================
# PROGRAMMER BEHAVIOR MIXTURES
# =========================================================
#
# Each programmer belongs to a hidden behavioral region.
#
# IMPORTANT:
#
# These labels are NOT stored in the ML dataset.
#
# K-Means will only see the resulting feature vectors.
# =========================================================

BEHAVIOR_PROFILES = [

    {
        "brute_force": 0.55,
        "hashing": 0.10,
        "binary_search": 0.05,
        "two_pointer": 0.05,
        "sliding_window": 0.05,
        "recursion": 0.05,
        "graph": 0.05,
        "dynamic_programming": 0.05,
        "data_structures": 0.05,
        "sorting": 0.00
    },

    {
        "brute_force": 0.05,
        "hashing": 0.25,
        "binary_search": 0.20,
        "two_pointer": 0.20,
        "sliding_window": 0.15,
        "recursion": 0.00,
        "graph": 0.05,
        "dynamic_programming": 0.05,
        "data_structures": 0.05,
        "sorting": 0.00
    },

    {
        "brute_force": 0.05,
        "hashing": 0.05,
        "binary_search": 0.05,
        "two_pointer": 0.05,
        "sliding_window": 0.05,
        "recursion": 0.35,
        "graph": 0.15,
        "dynamic_programming": 0.10,
        "data_structures": 0.15,
        "sorting": 0.05
    },

    {
        "brute_force": 0.05,
        "hashing": 0.15,
        "binary_search": 0.05,
        "two_pointer": 0.05,
        "sliding_window": 0.05,
        "recursion": 0.05,
        "graph": 0.15,
        "dynamic_programming": 0.20,
        "data_structures": 0.20,
        "sorting": 0.05
    },

    {
        "brute_force": 0.10,
        "hashing": 0.15,
        "binary_search": 0.10,
        "two_pointer": 0.10,
        "sliding_window": 0.10,
        "recursion": 0.05,
        "graph": 0.10,
        "dynamic_programming": 0.10,
        "data_structures": 0.10,
        "sorting": 0.10
    },

    {
        "brute_force": 0.05,
        "hashing": 0.10,
        "binary_search": 0.20,
        "two_pointer": 0.15,
        "sliding_window": 0.15,
        "recursion": 0.05,
        "graph": 0.05,
        "dynamic_programming": 0.10,
        "data_structures": 0.10,
        "sorting": 0.05
    }
]


# =========================================================
# HELPERS
# =========================================================

def choose_category(weights):

    categories = list(weights.keys())
    probabilities = list(weights.values())

    return random.choices(
        categories,
        weights=probabilities,
        k=1
    )[0]


def choose_programmer_profile():

    base = random.choice(
        BEHAVIOR_PROFILES
    )

    categories = list(base.keys())

    # Add small random variation
    raw = []

    for category in categories:

        value = max(
            0.001,
            base[category]
            + random.uniform(-0.04, 0.04)
        )

        raw.append(value)

    total = sum(raw)

    return {
        category: value / total
        for category, value
        in zip(categories, raw)
    }


# =========================================================
# DATABASE
# =========================================================

# Create a fresh database for this experiment.

db = Database(DB_PATH)

ast_analyzer = CodeAnalyzer()
complexity_analyzer = ComplexityAnalyzer()
behavior_analyzer = BehaviorAnalyzer()
feature_builder = MLFeatureBuilder()


# =========================================================
# GENERATE PROGRAMMERS
# =========================================================

print()
print("=" * 70)
print("GENERATING LARGE ML DATASET")
print("=" * 70)

print()
print(
    f"Programmers: {NUMBER_OF_PROGRAMMERS}"
)

print(
    f"Submissions per programmer: "
    f"{SUBMISSIONS_PER_PROGRAMMER}"
)

print(
    f"Expected submissions: "
    f"{NUMBER_OF_PROGRAMMERS * SUBMISSIONS_PER_PROGRAMMER}"
)


profiles = []


for programmer_number in range(
    1,
    NUMBER_OF_PROGRAMMERS + 1
):

    username = (
        f"programmer_{programmer_number:02d}"
    )

    weights = choose_programmer_profile()

    user_id = db.create_user(
        username
    )

    print()
    print(
        f"{username}"
    )

    # -----------------------------------------------------
    # Generate submissions
    # -----------------------------------------------------

    for submission_number in range(
        1,
        SUBMISSIONS_PER_PROGRAMMER + 1
    ):

        category = choose_category(
            weights
        )

        problem_name, code = random.choice(
            CODE_LIBRARY[category]
        )

        features = ast_analyzer.analyze(
            code
        )

        if not features["valid"]:
            continue

        complexity = (
            complexity_analyzer.analyze(
                code
            )
        )

        if not complexity["valid"]:
            continue

        db.save_features(
            db.save_submission(
                user_id=user_id,
                problem_name=(
                    f"{problem_name} "
                    f"{submission_number}"
                ),
                language="Python",
                code=code
            ),
            features,
            complexity
        )

    # -----------------------------------------------------
    # Build programmer profile
    # -----------------------------------------------------

    history = db.get_user_submissions(
        user_id
    )

    behavior = behavior_analyzer.analyze(
        history
    )

    if not behavior["valid"]:
        continue

    vector = feature_builder.build(
        behavior
    )

    profiles.append(
        {
            "username": username,
            "features": vector
        }
    )

    print(
        f"  submissions: {len(history)}"
    )

    print(
        f"  complexity: "
        f"{vector['average_complexity']}"
    )

    print(
        f"  optimization: "
        f"{vector['optimization_score']}"
    )

    print(
        f"  brute force: "
        f"{vector['brute_force_tendency']}"
    )


# =========================================================
# SUMMARY
# =========================================================

print()
print("=" * 70)
print("DATASET COMPLETE")
print("=" * 70)

print(
    f"Programmer profiles: "
    f"{len(profiles)}"
)

print(
    f"Total submissions: "
    f"{NUMBER_OF_PROGRAMMERS * SUBMISSIONS_PER_PROGRAMMER}"
)

print(
    f"Database: {DB_PATH}"
)


db.close()