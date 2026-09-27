from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------
# PROJECT ROOT
# ---------------------------------------------------------

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

db = Database("data/ml_dataset.db")

behavior_analyzer = BehaviorAnalyzer()
feature_builder = MLFeatureBuilder()


programmer_names = [
    "brute_force_dev",
    "optimization_dev",
    "recursive_dev",
    "data_structure_dev",
    "balanced_dev"
]


# =========================================================
# BUILD FEATURE MATRIX
# =========================================================

feature_rows = []
valid_names = []

for username in programmer_names:

    user = db.get_user(username)

    if not user:
        continue

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

    feature_rows.append(
        list(features.values())
    )

    valid_names.append(username)


X = np.array(feature_rows)


# =========================================================
# STANDARDIZE
# =========================================================

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)


# =========================================================
# TEST DIFFERENT K VALUES
# =========================================================

print()
print("=" * 70)
print("K-MEANS CLUSTER EVALUATION")
print("=" * 70)

print()

scores = {}

# With 5 programmers we can test k = 2, 3, 4.
# k = 5 would give every programmer their own cluster,
# which isn't useful for this demonstration.

for k in range(2, min(5, len(X))):

    model = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10
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
        f"k = {k}   "
        f"Silhouette Score = {score:.4f}"
    )


# =========================================================
# BEST K
# =========================================================

best_k = max(
    scores,
    key=scores.get
)

print()
print(
    f"Best k according to silhouette score: {best_k}"
)


# =========================================================
# FINAL MODEL
# =========================================================

model = KMeans(
    n_clusters=best_k,
    random_state=42,
    n_init=10
)

labels = model.fit_predict(
    X_scaled
)


print()
print("FINAL CLUSTER ASSIGNMENTS")
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
# PCA
# =========================================================

pca = PCA(
    n_components=2,
    random_state=42
)

X_pca = pca.fit_transform(
    X_scaled
)


print()
print("PCA")
print("-" * 70)

print(
    "Explained variance:",
    round(
        sum(pca.explained_variance_ratio_) * 100,
        2
    ),
    "%"
)


# =========================================================
# DISPLAY PCA COORDINATES
# =========================================================

print()
print("PCA COORDINATES")
print("-" * 70)

for username, label, point in zip(
    valid_names,
    labels,
    X_pca
):

    print(
        f"{username:<25} "
        f"Cluster {label}   "
        f"X={point[0]:.3f}   "
        f"Y={point[1]:.3f}"
    )


# =========================================================
# PLOT
# =========================================================

import matplotlib.pyplot as plt

plt.figure(figsize=(10, 7))

for cluster_id in range(best_k):

    indices = np.where(
        labels == cluster_id
    )[0]

    plt.scatter(
        X_pca[indices, 0],
        X_pca[indices, 1],
        s=120,
        label=f"Cluster {cluster_id}"
    )

    for index in indices:

        plt.annotate(
            valid_names[index],
            (
                X_pca[index, 0],
                X_pca[index, 1]
            ),
            xytext=(6, 6),
            textcoords="offset points"
        )


plt.xlabel("Principal Component 1")
plt.ylabel("Principal Component 2")

plt.title(
    "AI Programmer Behavior — K-Means Clusters"
)

plt.legend()

plt.grid(
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    "ml/programmer_clusters.png",
    dpi=150
)

plt.show()


db.close()