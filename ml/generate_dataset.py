from __future__ import annotations
import sys
from pathlib import Path

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
# SETUP
# =========================================================

db = Database("data/ml_dataset.db")

ast_analyzer = CodeAnalyzer()
complexity_analyzer = ComplexityAnalyzer()
behavior_analyzer = BehaviorAnalyzer()
feature_builder = MLFeatureBuilder()


# =========================================================
# SYNTHETIC PROGRAMMER PROFILES
# =========================================================
#
# These are NOT fake feature vectors.
# Every profile contains actual Python programs.
#
# The analyzers will extract the features.
# =========================================================

programmers = {

    "brute_force_dev": [

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
        ),

        (
            "Duplicate Check",
            """
def has_duplicate(nums):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] == nums[j]:
                return True

    return False
"""
        )
    ],

    # -----------------------------------------------------

    "optimization_dev": [

        (
            "Hash Two Sum",
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
            "Sliding Window",
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
        )
    ],

    # -----------------------------------------------------

    "recursive_dev": [

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

    return fibonacci(n - 1) + fibonacci(n - 2)
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

    "data_structure_dev": [

        (
            "Frequency Map",
            """
def frequency(nums):
    counts = {}

    for value in nums:
        counts[value] = counts.get(value, 0) + 1

    return counts
"""
        ),

        (
            "Set Operations",
            """
def unique_values(nums):
    seen = set()

    for value in nums:
        seen.add(value)

    return list(seen)
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
        )
    ],

    # -----------------------------------------------------

    "balanced_dev": [

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
            "Frequency",
            """
def count_values(nums):
    counts = {}

    for value in nums:
        counts[value] = counts.get(value, 0) + 1

    return counts
"""
        ),

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
        )
    ]
}


# =========================================================
# CREATE USERS + ANALYZE
# =========================================================

print()
print("=" * 70)
print("GENERATING ML PROGRAMMER DATASET")
print("=" * 70)


profiles = []


for username, submissions in programmers.items():

    print()
    print(f"PROGRAMMER: {username}")
    print("-" * 70)

    # -----------------------------------------------------
    # Create user
    # -----------------------------------------------------

    existing = db.get_user(username)

    if existing:
        user_id = existing["id"]

    else:
        user_id = db.create_user(username)

    # -----------------------------------------------------
    # Add submissions
    # -----------------------------------------------------

    for problem_name, code in submissions:

        features = ast_analyzer.analyze(code)

        if not features["valid"]:
            print(
                f"  FAILED AST: {problem_name}"
            )
            continue

        complexity = complexity_analyzer.analyze(code)

        if not complexity["valid"]:
            print(
                f"  FAILED COMPLEXITY: {problem_name}"
            )
            continue

        submission_id = db.save_submission(
            user_id=user_id,
            problem_name=problem_name,
            language="Python",
            code=code
        )

        db.save_features(
            submission_id=submission_id,
            features=features,
            complexity=complexity
        )

        print(
            f"  ✓ {problem_name}"
        )

    # -----------------------------------------------------
    # Analyze programmer history
    # -----------------------------------------------------

    history = db.get_user_submissions(user_id)

    behavior = behavior_analyzer.analyze(history)

    if not behavior["valid"]:
        print("  Behavior analysis failed.")
        continue

    vector = feature_builder.build(behavior)

    profiles.append({
        "username": username,
        "features": vector,
        "behavior": behavior
    })


# =========================================================
# DISPLAY DATASET
# =========================================================

print()
print("=" * 70)
print("ML DATASET")
print("=" * 70)

print(
    f"\nProgrammer profiles generated: {len(profiles)}"
)

for profile in profiles:

    print()
    print(profile["username"])

    for name, value in profile["features"].items():

        print(
            f"  {name:<32}: {value}"
        )


db.close()