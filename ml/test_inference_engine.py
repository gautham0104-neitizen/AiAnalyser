import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent)
)

from ml.inference_engine import InferenceEngine



code = """
def two_sum(nums, target):

    seen = {}

    for i, value in enumerate(nums):

        needed = target - value

        if needed in seen:
            return [seen[needed], i]

        seen[value] = i

    return []
"""


engine = InferenceEngine()

result = engine.analyze_code(code)


print()
print("=" * 60)
print("SINGLE CODE ANALYSIS")
print("=" * 60)

print()

print(
    "Valid:",
    result["valid"]
)

if not result["valid"]:

    print(
        "Error:",
        result["error"]
    )

    raise SystemExit(1)


print()
print("FEATURES")
print("-" * 60)

for name, value in result[
    "features"
].items():

    print(
        f"{name:<32}: {value}"
    )


print()
print(
    "ML VECTOR"
)

print("-" * 60)

print(
    engine.build_vector(result)
)

prediction = engine.predict(
    result
)

print()
print("## ML PREDICTION")

print(
    "Predicted cluster:",
    prediction["cluster"]
)

print()

print("Cluster memberships:")

for i, membership in enumerate(
    prediction["memberships"]
):

    print(
        f"Cluster {i}: "
        f"{membership * 100:.2f}%"
    )