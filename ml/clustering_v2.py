from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent)
)

import numpy as np

from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from backend.analyzer.behavior import BehaviorAnalyzer
from backend.database.database import Database
from ml.feature_builder import MLFeatureBuilder


# =========================================================
# SETUP
# =========================================================

DB_PATH = "data/ml_dataset_v2.db"

db = Database(DB_PATH)

behavior_analyzer = BehaviorAnalyzer()
feature_builder = MLFeatureBuilder()


# =========================================================
# GET ALL USERS
# =========================================================

cursor = db.connection.cursor()

cursor.execute("""
    SELECT id, username
    FROM users
    ORDER BY id
""")

users = cursor.fetchall()

print()
print("=" * 70)
print("PROGRAMMER CLUSTERING — LARGE DATASET")
print("=" * 70)

print()
print("Programmers found:", len(users))


# =========================================================
# BUILD FEATURE MATRIX
# =========================================================

feature_rows = []
programmer_names = []


for user in users:

    user_id = user["id"]
    username = user["username"]

    history = db.get_user_submissions(
        user_id
    )

    behavior = behavior_analyzer.analyze(
        history
    )

    if not behavior["valid"]:
        continue

    features = feature_builder.build(
        behavior
    )

    feature_rows.append(
        list(features.values())
    )

    programmer_names.append(
        username
    )


X = np.array(feature_rows)


print(
    "Feature matrix:",
    X.shape
)


# =========================================================
# STANDARDIZE
# =========================================================

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)


# =========================================================
# FIND BEST K
# =========================================================

print()
print("=" * 70)
print("TESTING CLUSTER COUNTS")
print("=" * 70)

scores = {}

max_k = min(
    8,
    len(X) - 1
)

for k in range(2, max_k + 1):

    model = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=20
    )

    labels = model.fit_predict(
        X_scaled
    )

    score = silhouette_score(
        X_scaled,
        labels
    )

    scores[k] = score

    print(
        f"k = {k:<3} "
        f"Silhouette Score = {score:.4f}"
    )


# =========================================================
# BEST K
# =========================================================

best_k = max(
    scores,
    key=scores.get
)

best_score = scores[best_k]


print()
print(
    f"BEST K: {best_k}"
)

print(
    f"BEST SILHOUETTE SCORE: "
    f"{best_score:.4f}"
)


# =========================================================
# FINAL MODEL
# =========================================================

model = KMeans(
    n_clusters=best_k,
    random_state=42,
    n_init=20
)

labels = model.fit_predict(
    X_scaled
)


# =========================================================
# CLUSTER MEMBERS
# =========================================================

clusters = {}

for username, label in zip(
    programmer_names,
    labels
):

    clusters.setdefault(
        int(label),
        []
    ).append(username)


print()
print("=" * 70)
print("CLUSTER MEMBERS")
print("=" * 70)


for cluster_id in sorted(
    clusters
):

    members = clusters[
        cluster_id
    ]

    print()
    print(
        f"Cluster {cluster_id} "
        f"({len(members)} programmers)"
    )

    print("-" * 50)

    for member in members:

        print(
            "  •",
            member
        )


# =========================================================
# CLUSTER CENTERS
# =========================================================

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


centers = scaler.inverse_transform(
    model.cluster_centers_
)


print()
print("=" * 70)
print("CLUSTER CHARACTERISTICS")
print("=" * 70)


for cluster_id, center in enumerate(
    centers
):

    print()
    print(
        f"CLUSTER {cluster_id}"
    )

    print("-" * 50)

    for name, value in zip(
        feature_names,
        center
    ):

        print(
            f"{name:<32}: "
            f"{value:.2f}"
        )


# =========================================================
# PCA
# =========================================================

pca = PCA(
    n_components=2
)

X_pca = pca.fit_transform(
    X_scaled
)


explained_variance = (
    sum(
        pca.explained_variance_ratio_
    )
    * 100
)


print()
print("=" * 70)
print("PCA")
print("=" * 70)

print(
    "Explained variance:",
    round(
        explained_variance,
        2
    ),
    "%"
)


# =========================================================
# SAVE PCA DATA
# =========================================================

with open(
    "ml/pca_results.csv",
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "username,cluster,pc1,pc2\n"
    )

    for username, label, point in zip(
        programmer_names,
        labels,
        X_pca
    ):

        file.write(
            f"{username},"
            f"{label},"
            f"{point[0]:.6f},"
            f"{point[1]:.6f}\n"
        )


# =========================================================
# VISUALIZATION
# =========================================================

import matplotlib.pyplot as plt


plt.figure(
    figsize=(12, 8)
)


for cluster_id in range(
    best_k
):

    indices = np.where(
        labels == cluster_id
    )[0]

    plt.scatter(
        X_pca[indices, 0],
        X_pca[indices, 1],
        s=90,
        label=f"Cluster {cluster_id}"
    )

    for index in indices:

        plt.annotate(
            programmer_names[index],
            (
                X_pca[index, 0],
                X_pca[index, 1]
            ),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8
        )


plt.xlabel(
    "Principal Component 1"
)

plt.ylabel(
    "Principal Component 2"
)

plt.title(
    "AI Programmer Behavior — "
    "K-Means Clustering"
)

plt.legend()

plt.grid(
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    "ml/programmer_clusters_v2.png",
    dpi=180
)

plt.show()


# =========================================================
# CLOSE
# =========================================================

db.close()