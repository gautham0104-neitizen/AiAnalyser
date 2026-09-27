from __future__ import annotations

import sys
from pathlib import Path
import pickle

import numpy as np

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

# ---------------------------------------------------------
# PROJECT ROOT
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)

# ---------------------------------------------------------
# IMPORT PROJECT COMPONENTS
# ---------------------------------------------------------

from backend.analyzer.behavior import BehaviorAnalyzer
from backend.database.database import Database
from ml.feature_builder import MLFeatureBuilder


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

DB_PATH = PROJECT_ROOT / "data" / "ml_dataset_v2.db"

MODEL_DIR = PROJECT_ROOT / "models"

MODEL_PATH = MODEL_DIR / "kmeans_model.pkl"

SCALER_PATH = MODEL_DIR / "scaler.pkl"


# ---------------------------------------------------------
# SETUP
# ---------------------------------------------------------

MODEL_DIR.mkdir(
    exist_ok=True
)

db = Database(
    str(DB_PATH)
)

behavior_analyzer = BehaviorAnalyzer()

feature_builder = MLFeatureBuilder()


# ---------------------------------------------------------
# GET USERS
# ---------------------------------------------------------

cursor = db.connection.cursor()

cursor.execute("""
    SELECT id, username
    FROM users
    ORDER BY id
""")

users = cursor.fetchall()


print()
print("=" * 70)
print("TRAINING ML MODEL")
print("=" * 70)

print()

print(
    "Programmers found:",
    len(users)
)


# ---------------------------------------------------------
# BUILD FEATURE MATRIX
# ---------------------------------------------------------

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


X = np.array(
    feature_rows
)


print(
    "Feature matrix:",
    X.shape
)


# ---------------------------------------------------------
# STANDARDIZE FEATURES
# ---------------------------------------------------------

scaler = StandardScaler()

X_scaled = scaler.fit_transform(
    X
)


# ---------------------------------------------------------
# FIND BEST K
# ---------------------------------------------------------

print()
print(
    "Testing cluster counts..."
)

scores = {}

max_k = min(
    8,
    len(X) - 1
)


for k in range(
    2,
    max_k + 1
):

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


# ---------------------------------------------------------
# PRODUCTION CLUSTER COUNT
# ---------------------------------------------------------
# The application uses 5 stable behavioral profiles.
# We still evaluate multiple K values above, but the
# production model always uses 5 clusters.

best_k = 5

best_score = scores[
    best_k
]


print()

print(
    "BEST K:",
    best_k
)

print(
    "BEST SILHOUETTE SCORE:",
    f"{best_score:.4f}"
)


# ---------------------------------------------------------
# TRAIN FINAL MODEL
# ---------------------------------------------------------

model = KMeans(
    n_clusters=best_k,
    random_state=42,
    n_init=20
)

model.fit(
    X_scaled
)


# ---------------------------------------------------------
# SAVE MODEL
# ---------------------------------------------------------

with open(
    MODEL_PATH,
    "wb"
) as file:

    pickle.dump(
        model,
        file
    )


# ---------------------------------------------------------
# SAVE SCALER
# ---------------------------------------------------------

with open(
    SCALER_PATH,
    "wb"
) as file:

    pickle.dump(
        scaler,
        file
    )


# ---------------------------------------------------------
# VERIFY
# ---------------------------------------------------------

print()

print(
    "=" * 70
)

print(
    "MODEL SAVED"
)

print(
    "=" * 70
)

print()

print(
    "Model:",
    MODEL_PATH
)

print(
    "Scaler:",
    SCALER_PATH
)

print()

print(
    "Clusters:",
    model.n_clusters
)

print(
    "Features:",
    X.shape[1]
)

print(
    "Silhouette:",
    f"{best_score:.4f}"
)


# ---------------------------------------------------------
# CLOSE DATABASE
# ---------------------------------------------------------

db.close()