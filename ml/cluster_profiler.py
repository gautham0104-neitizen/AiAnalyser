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

from backend.analyzer.behavior import BehaviorAnalyzer
from backend.database.database import Database
from ml.feature_builder import MLFeatureBuilder


# =========================================================
# CONFIG
# =========================================================

DB_PATH = "data/ml_dataset_v2.db"
K = 5

db = Database(DB_PATH)

behavior_analyzer = BehaviorAnalyzer()
feature_builder = MLFeatureBuilder()


# =========================================================
# FEATURES
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
# GET USERS
# =========================================================

cursor = db.connection.cursor()

cursor.execute("""
    SELECT id, username
    FROM users
    ORDER BY id
""")

users = cursor.fetchall()


# =========================================================
# BUILD FEATURE MATRIX
# =========================================================

feature_rows = []
programmer_names = []


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

    feature_rows.append(
        [
            features[name]
            for name in FEATURE_NAMES
        ]
    )

    programmer_names.append(
        user["username"]
    )


X = np.array(feature_rows)


# =========================================================
# SCALE
# =========================================================

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)


# =========================================================
# K-MEANS
# =========================================================

model = KMeans(
    n_clusters=K,
    random_state=42,
    n_init=20
)

labels = model.fit_predict(
    X_scaled
)


# =========================================================
# RAW CLUSTER CENTERS
# =========================================================
#
# K-Means works on standardized data.
# We convert the centers back to the
# original feature scale for interpretation.
# =========================================================

centers_raw = scaler.inverse_transform(
    model.cluster_centers_
)


# =========================================================
# HELPER
# =========================================================

def value(
    center,
    feature_name
):

    index = FEATURE_NAMES.index(
        feature_name
    )

    return center[index]


# =========================================================
# SMART PROFILE NAMING
# =========================================================

def determine_profile(
    center
):

    recursion = value(
        center,
        "recursion_percentage"
    )

    brute_force = value(
        center,
        "brute_force_tendency"
    )

    nested_loops = value(
        center,
        "nested_loop_percentage"
    )

    optimization = value(
        center,
        "optimization_score"
    )

    algorithm_diversity = value(
        center,
        "algorithm_diversity"
    )

    data_structures = value(
        center,
        "data_structure_diversity"
    )

    maintainability = value(
        center,
        "average_maintainability"
    )

    improvement = value(
        center,
        "improvement_score"
    )

    # -----------------------------------------------------
    # Find dominant characteristics
    # -----------------------------------------------------

    characteristics = []

    # Recursive
    if recursion >= 30:
        characteristics.append(
            "recursive problem solving"
        )

    # Brute force
    if brute_force >= 25:
        characteristics.append(
            "high brute-force tendency"
        )

    # Nested loops
    if nested_loops >= 30:
        characteristics.append(
            "frequent nested-loop usage"
        )

    # Optimization
    if optimization >= 60:
        characteristics.append(
            "optimization-oriented thinking"
        )

    # Algorithm diversity
    if algorithm_diversity >= 70:
        characteristics.append(
            "high algorithmic diversity"
        )

    # Data structures
    if data_structures >= 50:
        characteristics.append(
            "broad data-structure usage"
        )

    # Code quality
    if maintainability >= 82:
        characteristics.append(
            "strong code maintainability"
        )

    # Improvement
    if improvement >= 60:
        characteristics.append(
            "strong improvement trend"
        )

    # -----------------------------------------------------
    # Determine profile
    # -----------------------------------------------------

    if (
        brute_force >= 30
        and nested_loops >= 30
    ):

        profile = (
            "Brute Force Specialist"
        )

    elif recursion >= 35:

        profile = (
            "Recursive Algorithmist"
        )

    elif (
        algorithm_diversity >= 75
        and improvement >= 60
    ):

        profile = (
            "Algorithm Explorer"
        )

    elif (
        maintainability >= 82
        and data_structures >= 50
    ):

        profile = (
            "Clean Code Specialist"
        )

    elif optimization >= 60:

        profile = (
            "Optimization Specialist"
        )

    else:

        profile = (
            "Balanced Programmer"
        )

    return profile, characteristics


# =========================================================
# BUILD PROFILES
# =========================================================

cluster_profiles = {}


print()
print("=" * 70)
print("AI PROGRAMMER CLUSTER PROFILES")
print("=" * 70)


for cluster_id in range(K):

    center = centers_raw[
        cluster_id
    ]

    profile, characteristics = (
        determine_profile(center)
    )

    cluster_profiles[
        cluster_id
    ] = {
        "profile": profile,
        "characteristics": characteristics
    }

    members = [
        programmer_names[i]
        for i in range(
            len(programmer_names)
        )
        if labels[i] == cluster_id
    ]

    print()
    print(
        f"CLUSTER {cluster_id}"
    )

    print("-" * 70)

    print(
        "Profile:",
        profile
    )

    print(
        "Members:",
        len(members)
    )

    print()
    print(
        "Characteristics:"
    )

    for characteristic in characteristics:

        print(
            f"  ✓ {characteristic}"
        )

    print()
    print(
        "Members:"
    )

    for member in members:

        print(
            f"  • {member}"
        )


# =========================================================
# RELATIVE MEMBERSHIP
# =========================================================

def get_membership_scores(
    programmer_index
):

    point = X_scaled[
        programmer_index
    ]

    distances = []

    for center in model.cluster_centers_:

        distance = np.linalg.norm(
            point - center
        )

        distances.append(
            distance
        )

    distances = np.array(
        distances
    )

    # Convert distance into similarity.
    #
    # Smaller distance = higher similarity.
    similarities = np.exp(
        -distances
    )

    probabilities = (
        similarities
        / similarities.sum()
    )

    return probabilities


# =========================================================
# PROGRAMMER PROFILE
# =========================================================

def get_programmer_profile(
    programmer_index
):

    probabilities = (
        get_membership_scores(
            programmer_index
        )
    )

    best_cluster = int(
        np.argmax(probabilities)
    )

    cluster_info = (
        cluster_profiles[
            best_cluster
        ]
    )

    return {
        "programmer":
            programmer_names[
                programmer_index
            ],

        "cluster":
            best_cluster,

        "profile":
            cluster_info["profile"],

        "membership":
            float(
                probabilities[
                    best_cluster
                ]
                * 100
            ),

        "all_clusters":
            probabilities * 100,

        "characteristics":
            cluster_info[
                "characteristics"
            ]
    }


# =========================================================
# EXAMPLES
# =========================================================

print()
print("=" * 70)
print("PROGRAMMER AI PROFILES")
print("=" * 70)


examples = [
    0,
    7,
    15,
    20,
    29
]


for index in examples:

    result = (
        get_programmer_profile(
            index
        )
    )

    print()
    print(
        result["programmer"]
    )

    print(
        "Profile:",
        result["profile"]
    )

    print(
        "Primary cluster:",
        result["cluster"]
    )

    print(
        "Membership:",
        f"{result['membership']:.2f}%"
    )

    print()
    print(
        "Cluster membership:"
    )

    for cluster_id, score in enumerate(
        result["all_clusters"]
    ):

        print(
            f"  Cluster {cluster_id}: "
            f"{score:.2f}%"
        )

    print()
    print(
        "Characteristics:"
    )

    for characteristic in result[
        "characteristics"
    ]:

        print(
            f"  ✓ {characteristic}"
        )


db.close()