import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent)
)

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from backend.analyzer.behavior import BehaviorAnalyzer
from backend.database.database import Database

from ml.feature_builder import MLFeatureBuilder
from ml.inference_engine import InferenceEngine


# =========================================================
# CONFIGURATION
# =========================================================

DB_PATH = "data/ml_dataset_v2.db"
K = 5


# =========================================================
# PROFILE NAMES
# =========================================================

PROFILES = {
    0: "Recursive Algorithmist",
    1: "Optimization Specialist",
    2: "Brute Force Specialist",
    3: "Algorithm Explorer",
    4: "Clean Code Specialist"
}


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
# NEW CODE
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
# DATABASE
# =========================================================

db = Database(DB_PATH)

behavior_analyzer = BehaviorAnalyzer()
feature_builder = MLFeatureBuilder()


# =========================================================
# BUILD TRAINING DATA
# =========================================================

cursor = db.connection.cursor()

cursor.execute("""
    SELECT id, username
    FROM users
    ORDER BY id
""")

users = cursor.fetchall()

training_vectors = []

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

    vector = [
        features[name]
        for name in FEATURE_NAMES
    ]

    training_vectors.append(vector)


X = np.array(training_vectors)


print()
print("=" * 70)
print("TRAINING PROGRAMMER BEHAVIOR MODEL")
print("=" * 70)

print()
print(
    "Programmers:",
    len(X)
)

print(
    "Features:",
    X.shape[1]
)


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


print()
print(
    "K-Means trained."
)


# =========================================================
# ANALYZE NEW CODE
# =========================================================

print()
print("=" * 70)
print("ANALYZING NEW CODE")
print("=" * 70)


engine = InferenceEngine()

analysis = engine.analyze_code(
    NEW_CODE
)


if not analysis["valid"]:

    print()
    print(
        "Analysis failed:"
    )

    print(
        analysis["error"]
    )

    db.close()

    raise SystemExit(1)


# =========================================================
# GET NEW CODE VECTOR
# =========================================================

new_vector = engine.build_vector(
    analysis
)


print()
print(
    "New code vector created."
)


# =========================================================
# SCALE USING TRAINING SCALER
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
# CALCULATE MEMBERSHIP
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


# Smaller distance = stronger membership

similarities = np.exp(
    -distances
)


membership = (
    similarities
    / similarities.sum()
)


# =========================================================
# FINAL RESULT
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
    PROFILES[
        predicted_cluster
    ]
)

print(
    "Primary membership:",
    f"{membership[predicted_cluster] * 100:.2f}%"
)


# =========================================================
# ALL CLUSTERS
# =========================================================

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
        f"→ "
        f"{PROFILES[cluster_id]}"
    )


# =========================================================
# CODE FEATURES
# =========================================================

print()
print(
    "CODE-LEVEL FEATURES"
)

print("-" * 70)

for name, value in analysis[
    "features"
].items():

    print(
        f"{name:<32}: {value}"
    )


# =========================================================
# CLOSE
# =========================================================

db.close()