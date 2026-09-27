from backend.analyzer.ast_analyzer import CodeAnalyzer
from backend.analyzer.complexity import ComplexityAnalyzer
from backend.database.database import Database


# ---------------------------------------------------------
# SETUP
# ---------------------------------------------------------

db = Database("data/test.db")

ast_analyzer = CodeAnalyzer()
complexity_analyzer = ComplexityAnalyzer()


# ---------------------------------------------------------
# CREATE USER
# ---------------------------------------------------------

user = db.get_user("Gautham")

if user:
    user_id = user["id"]
    print("Existing user:", user_id)
else:
    user_id = db.create_user("Gautham")
    print("Created user:", user_id)


# ---------------------------------------------------------
# SAMPLE PROGRAM
# ---------------------------------------------------------

code = """
def two_sum(nums, target):
    seen = {}

    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]

        seen[n] = i

    return []
"""


# ---------------------------------------------------------
# RUN AST ANALYZER
# ---------------------------------------------------------

features = ast_analyzer.analyze(code)

if not features["valid"]:
    print("AST analysis failed:")
    print(features["error"])
    db.close()
    raise SystemExit(1)


print("\nAST ANALYSIS")
print("=" * 50)

print("Functions:", features["num_functions"])
print("Loops:", features["total_loops"])
print("Nested loops:", features["nested_loops"])
print("Recursion:", features["recursive_functions"])

print("\nData Structures:")
print(features["data_structures"])

print("\nPatterns:")

for pattern in features["patterns"]:
    print(
        f"  {pattern['pattern']} "
        f"(confidence={pattern['confidence']})"
    )


# ---------------------------------------------------------
# RUN COMPLEXITY ANALYZER
# ---------------------------------------------------------

complexity = complexity_analyzer.analyze(code)

if not complexity["valid"]:
    print("Complexity analysis failed:")
    print(complexity["error"])
    db.close()
    raise SystemExit(1)


print("\nCOMPLEXITY ANALYSIS")
print("=" * 50)

print(
    "Average cyclomatic complexity:",
    complexity["cyclomatic_complexity"]["average"]
)

print(
    "Maximum cyclomatic complexity:",
    complexity["cyclomatic_complexity"]["maximum"]
)

print(
    "Maintainability index:",
    complexity["maintainability_index"]
)


# ---------------------------------------------------------
# SAVE SUBMISSION
# ---------------------------------------------------------

submission_id = db.save_submission(
    user_id=user_id,
    problem_name="Two Sum",
    language="Python",
    code=code
)

print("\nSubmission saved:", submission_id)


# ---------------------------------------------------------
# SAVE REAL ANALYSIS
# ---------------------------------------------------------

db.save_features(
    submission_id=submission_id,
    features=features,
    complexity=complexity
)

print("Real analysis saved to database.")


# ---------------------------------------------------------
# READ HISTORY
# ---------------------------------------------------------

history = db.get_user_submissions(user_id)

print("\nUSER HISTORY")
print("=" * 50)

for row in history:

    print(
        f"Submission {row['id']} | "
        f"{row['problem_name']} | "
        f"Complexity: {row['cyclomatic_complexity']} | "
        f"Maintainability: {row['maintainability_index']}"
    )


# ---------------------------------------------------------
# CLOSE
# ---------------------------------------------------------

db.close()