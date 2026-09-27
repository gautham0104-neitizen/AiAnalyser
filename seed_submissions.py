from backend.analyzer.ast_analyzer import CodeAnalyzer
from backend.analyzer.complexity import ComplexityAnalyzer
from backend.database.database import Database


db = Database("data/test.db")

ast_analyzer = CodeAnalyzer()
complexity_analyzer = ComplexityAnalyzer()


# ---------------------------------------------------------
# USER
# ---------------------------------------------------------

user = db.get_user("Gautham")

if user:
    user_id = user["id"]
else:
    user_id = db.create_user("Gautham")


# ---------------------------------------------------------
# REAL PROGRAMMING SUBMISSIONS
# ---------------------------------------------------------

programs = [

    (
        "Nested Loop Search",
        """
def find_common(a, b):
    result = []

    for x in a:
        for y in b:
            if x == y:
                result.append(x)

    return result
"""
    ),

    (
        "Frequency Counter",
        """
def frequency(nums):
    counts = {}

    for n in nums:
        counts[n] = counts.get(n, 0) + 1

    return counts
"""
    ),

    (
        "Binary Search",
        """
def binary_search(arr, target):
    left = 0
    right = len(arr) - 1

    while left <= right:
        mid = (left + right) // 2

        if arr[mid] == target:
            return mid

        if arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1

    return -1
"""
    ),

    (
        "Sorting",
        """
def sort_numbers(nums):
    nums = nums.copy()
    nums.sort()
    return nums
"""
    ),

    (
        "Factorial Recursion",
        """
def factorial(n):
    if n <= 1:
        return 1

    return n * factorial(n - 1)
"""
    ),

    (
        "Two Pointer",
        """
def two_sum_sorted(nums, target):
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
        "Brute Force Maximum",
        """
def max_pair_product(nums):
    best = 0

    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            product = nums[i] * nums[j]

            if product > best:
                best = product

    return best
"""
    ),

    (
        "Graph BFS",
        """
from collections import deque

def bfs(graph, start):
    visited = {start}
    queue = deque([start])
    order = []

    while queue:
        node = queue.popleft()
        order.append(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return order
"""
    ),

    (
        "Dynamic Programming",
        """
def fibonacci(n):
    if n <= 1:
        return n

    dp = [0] * (n + 1)
    dp[1] = 1

    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]

    return dp[n]
"""
    ),

    (
        "Sliding Window",
        """
def max_sum(nums, k):
    if k > len(nums):
        return 0

    window = sum(nums[:k])
    best = window

    for end in range(k, len(nums)):
        window += nums[end]
        window -= nums[end - k]

        best = max(best, window)

    return best
"""
    )
]


# ---------------------------------------------------------
# ANALYZE AND STORE
# ---------------------------------------------------------

print("\nSEEDING DATABASE")
print("=" * 60)

for problem_name, code in programs:

    # AST analysis
    features = ast_analyzer.analyze(code)

    if not features["valid"]:
        print(f"FAILED AST: {problem_name}")
        continue

    # Complexity analysis
    complexity = complexity_analyzer.analyze(code)

    if not complexity["valid"]:
        print(f"FAILED COMPLEXITY: {problem_name}")
        continue

    # Save submission
    submission_id = db.save_submission(
        user_id=user_id,
        problem_name=problem_name,
        language="Python",
        code=code
    )

    # Save actual analysis
    db.save_features(
        submission_id=submission_id,
        features=features,
        complexity=complexity
    )

    print(
        f"✓ {problem_name:<25} "
        f"Complexity: "
        f"{complexity['cyclomatic_complexity']['average']}"
    )


# ---------------------------------------------------------
# SHOW HISTORY
# ---------------------------------------------------------

history = db.get_user_submissions(user_id)

print("\n")
print("TOTAL SUBMISSIONS:", len(history))

print("\nPROGRAMMING HISTORY")
print("=" * 60)

for row in history:

    print(
        f"{row['problem_name']:<25} "
        f"Complexity: {row['cyclomatic_complexity']:<5} "
        f"Maintainability: {row['maintainability_index']}"
    )


db.close()