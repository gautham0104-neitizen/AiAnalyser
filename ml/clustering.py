from __future__ import annotations

import sys
from pathlib import Path

# Make project root available
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


# =========================================================
# SETUP
# =========================================================

db = Database("data/ml_dataset.db")

behavior_analyzer = BehaviorAnalyzer()
feature_builder = MLFeatureBuilder()


# =========================================================
# PROGRAMMERS
# =========================================================

programmer_names = [
    "brute_force_dev",
    "optimization_dev",
    "recursive_dev",
    "data_structure_dev",
    "balanced_dev"
]


feature_rows = []
valid_names = []


# =========================================================
# BUILD FEATURE MATRIX
# =========================================================

for username in programmer_names:

    user = db.get_user(username)

    if not user:
        print(f"User not found: {username}")
        continue

    history = db.get_user_submissions(
        user["id"]
    )

    behavior = behavior_analyzer.analyze(
        history
    )

    if not behavior["valid"]:
        print(
            f"Behavior analysis failed: {username}"
        )
        continue

    features = feature_builder.build(
        behavior
    )

    feature_rows.append(
        list(features.values())
    )

    valid_names.append(username)


# =========================================================
# CHECK DATASET
# =========================================================

if len(feature_rows) < 3:

    print(
        "Need at least 3 programmer profiles "
        "for clustering."
    )

    db.close()
    raise SystemExit(1)


X = np.array(feature_rows)

print()
print("=" * 70)
print("K-MEANS PROGRAMMER CLUSTERING")
print("=" * 70)

print()
print("Programmers:", len(valid_names))
print("Features:", X.shape[1])


# =========================================================
# STANDARDIZE FEATURES
# =========================================================

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)


# =========================================================
# K-MEANS
# =========================================================

number_of_clusters = 3

model = KMeans(
    n_clusters=number_of_clusters,
    random_state=42,
    n_init=10
)

labels = model.fit_predict(
    X_scaled
)


# =========================================================
# RESULTS
# =========================================================

print()
print("CLUSTER ASSIGNMENTS")
print("-" * 70)

for username, label in zip(
    valid_names,
    labels
):

    print(
        f"{username:<25} "
        f"Cluster {label}"
    )


# =========================================================
# CLUSTER CONTENT
# =========================================================

print()
print("CLUSTER MEMBERS")
print("-" * 70)

clusters = {}

for username, label in zip(
    valid_names,
    labels
):

    clusters.setdefault(
        int(label),
        []
    ).append(username)


for cluster_id, members in clusters.items():

    print(
        f"\nCluster {cluster_id}:"
    )

    for member in members:

        print(
            f"  • {member}"
        )


# =========================================================
# CLUSTER CENTERS
# =========================================================

print()
print("CLUSTER CENTERS")
print("-" * 70)

feature_names = [
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


# Convert centers back to original scale
centers = scaler.inverse_transform(
    model.cluster_centers_
)


for cluster_id, center in enumerate(
    centers
):

    print(
        f"\nCluster {cluster_id}"
    )

    for name, value in zip(
        feature_names,
        center
    ):

        print(
            f"  {name:<32}: "
            f"{value:.2f}"
        )


# =========================================================
# INERTIA
# =========================================================

print()
print("MODEL INFORMATION")
print("-" * 70)

print(
    "Inertia:",
    round(model.inertia_, 4)
)

print(
    "Number of clusters:",
    number_of_clusters
)


db.close()