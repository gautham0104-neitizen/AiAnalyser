from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent)
)

import numpy as np

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from backend.analyzer.ast_analyzer import CodeAnalyzer
from backend.analyzer.complexity import ComplexityAnalyzer
from backend.analyzer.behavior import BehaviorAnalyzer
from backend.database.database import Database

from ml.feature_builder import MLFeatureBuilder


# =========================================================
# CONFIG
# =========================================================

DB_PATH = "data/ml_dataset_v2.db"
K = 5


# =========================================================
# NEW CODE TO ANALYZE
# =========================================================
#
# Change this code whenever you want to test
# another programmer.
# =========================================================

NEW_CODE = """
def two_sum(nums, target):

    seen = {}

    for i, value in enumerate(nums):

        needed = target - value

        if needed in seen:
            return [seen[needed], i]

        seen[value] = i

    return []
"""


# =========================================================
# SETUP
# =========================================================

db = Database(DB_PATH)

ast_analyzer = CodeAnalyzer()
complexity_analyzer = ComplexityAnalyzer()
behavior_analyzer = BehaviorAnalyzer()
feature_builder = MLFeatureBuilder()


# =========================================================
# FEATURE NAMES
# =========================================================

FEATURE_NAMES = [
    "average_complexity",
    "average_maintainability",
    "nested_loop_percentage",
    "recursion_percentage",
    "algorithm_diversity",
    "data_structure_diversity",
    "brute_force_tendency",
    "optimization_score",
    "code_quality_score",
    "problem_solving_diversity",
    "improvement_score"
]


# =========================================================
# TRAIN K-MEANS FROM EXISTING PROGRAMMERS
# =========================================================

cursor = db.connection.cursor()

cursor.execute("""
    SELECT id, username
    FROM users
    ORDER BY id
""")

users = cursor.fetchall()


training_rows = []
training_names = []


for user in users:

    history = db.get_user_submissions(
        user["id"]
    )

    behavior = behavior_analyzer.analyze(
        history
    )

    if not behavior["valid"]:
        continue

    features = feature_builder.build(
        behavior
    )

    training_rows.append(
        [
            features[name]
            for name in FEATURE_NAMES
        ]
    )

    training_names.append(
        user["username"]
    )


X = np.array(training_rows)


# =========================================================
# SCALE TRAINING DATA
# =========================================================

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)


# =========================================================
# TRAIN K-MEANS
# =========================================================

model = KMeans(
    n_clusters=K,
    random_state=42,
    n_init=20
)

model.fit(X_scaled)


# =========================================================
# ANALYZE NEW CODE
# =========================================================

print()
print("=" * 70)
print("ANALYZING NEW CODE")
print("=" * 70)


# ---------------------------------------------------------
# AST
# ---------------------------------------------------------

ast_result = ast_analyzer.analyze(
    NEW_CODE
)

if not ast_result["valid"]:

    print(
        "AST analysis failed:"
    )

    print(
        ast_result["error"]
    )

    db.close()
    raise SystemExit(1)


# ---------------------------------------------------------
# COMPLEXITY
# ---------------------------------------------------------

complexity_result = (
    complexity_analyzer.analyze(
        NEW_CODE
    )
)

if not complexity_result["valid"]:

    print(
        "Complexity analysis failed:"
    )

    print(
        complexity_result["error"]
    )

    db.close()
    raise SystemExit(1)


# =========================================================
# BUILD SINGLE-CODE FEATURE VECTOR
# =========================================================
#
# The existing feature builder expects a
# programmer history, so we create a temporary
# in-memory history representation.
#
# Instead of saving this new code to the database,
# we derive its individual behavioral features.
# =========================================================

temporary_db = Database(
    "data/inference_temp.db"
)

temp_user = temporary_db.create_user(
    "__inference_user__"
)

submission_id = (
    temporary_db.save_submission(
        user_id=temp_user,
        problem_name="New Code",
        language="Python",
        code=NEW_CODE
    )
)

temporary_db.save_features(
    submission_id,
    ast_result,
    complexity_result
)

temporary_history = (
    temporary_db.get_user_submissions(
        temp_user
    )
)

temporary_behavior = (
    behavior_analyzer.analyze(
        temporary_history
    )
)

if not temporary_behavior["valid"]:

    print(
        "Behavior analysis failed."
    )

    temporary_db.close()
    db.close()

    raise SystemExit(1)


new_features = feature_builder.build(
    temporary_behavior
)


new_vector = np.array(
    [
        new_features[name]
        for name in FEATURE_NAMES
    ]
).reshape(1, -1)


# =========================================================
# SCALE NEW VECTOR
# =========================================================

new_vector_scaled = (
    scaler.transform(
        new_vector
    )
)


# =========================================================
# PREDICT CLUSTER
# =========================================================

predicted_cluster = int(
    model.predict(
        new_vector_scaled
    )[0]
)


# =========================================================
# MEMBERSHIP SCORES
# =========================================================

distances = []

for center in model.cluster_centers_:

    distance = np.linalg.norm(
        new_vector_scaled[0] - center
    )

    distances.append(
        distance
    )


distances = np.array(
    distances
)

similarities = np.exp(
    -distances
)

membership = (
    similarities
    / similarities.sum()
)


# =========================================================
# PROFILE DEFINITIONS
# =========================================================
#
# These correspond to the profiles we discovered
# from the cluster centers.
# =========================================================

profiles = {
    0: "Recursive Algorithmist",
    1: "Optimization Specialist",
    2: "Brute Force Specialist",
    3: "Algorithm Explorer",
    4: "Clean Code Specialist"
}


# =========================================================
# RESULTS
# =========================================================

print()
print("=" * 70)
print("AI PROGRAMMER PROFILE")
print("=" * 70)

print()

print(
    "Predicted cluster:",
    predicted_cluster
)

print(
    "Profile:",
    profiles[
        predicted_cluster
    ]
)

print(
    "Primary membership:",
    f"{membership[predicted_cluster] * 100:.2f}%"
)


print()
print(
    "CLUSTER MEMBERSHIP"
)

print("-" * 70)

for cluster_id, score in enumerate(
    membership
):

    print(
        f"Cluster {cluster_id}: "
        f"{score * 100:.2f}% "
        f"→ {profiles[cluster_id]}"
    )


# =========================================================
# CODE FEATURES
# =========================================================

print()
print(
    "EXTRACTED FEATURES"
)

print("-" * 70)

for name, value in new_features.items():

    print(
        f"{name:<32}: {value}"
    )


# =========================================================
# CLOSE
# =========================================================

temporary_db.close()
db.close()