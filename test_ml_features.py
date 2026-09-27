from backend.analyzer.behavior import BehaviorAnalyzer
from backend.database.database import Database

from ml.feature_builder import MLFeatureBuilder


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

db = Database("data/test.db")

user = db.get_user("Gautham")

if not user:
    print("User not found.")
    db.close()
    raise SystemExit(1)

user_id = user["id"]


# ---------------------------------------------------------
# GET HISTORY
# ---------------------------------------------------------

history = db.get_user_submissions(user_id)

print("SUBMISSIONS:", len(history))


# ---------------------------------------------------------
# BEHAVIOR ANALYSIS
# ---------------------------------------------------------

behavior_analyzer = BehaviorAnalyzer()

behavior = behavior_analyzer.analyze(history)

if not behavior["valid"]:
    print("Behavior analysis failed.")
    db.close()
    raise SystemExit(1)


# ---------------------------------------------------------
# BUILD ML FEATURES
# ---------------------------------------------------------

builder = MLFeatureBuilder()

features = builder.build(behavior)


# ---------------------------------------------------------
# DISPLAY
# ---------------------------------------------------------

print("\nML FEATURE VECTOR")
print("=" * 60)

for name, value in features.items():
    print(
        f"{name:<35}: {value}"
    )


db.close()