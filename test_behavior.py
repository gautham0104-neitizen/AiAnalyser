from backend.analyzer.behavior import BehaviorAnalyzer
from backend.database.database import Database


db = Database("data/test.db")

user = db.get_user("Gautham")

if not user:
    print("User not found.")
    db.close()
    raise SystemExit(1)

user_id = user["id"]

history = db.get_user_submissions(user_id)

print("SUBMISSIONS FOUND:", len(history))

analyzer = BehaviorAnalyzer()

result = analyzer.analyze(history)

print("\n")
print("AI PROGRAMMER BEHAVIOR ANALYSIS")
print("=" * 60)

if not result["valid"]:
    print("Analysis failed:")
    print(result["error"])
    db.close()
    raise SystemExit(1)


print("\nPROGRAMMING STYLE")
print("-" * 60)

print(
    result["programming_style"]["name"]
)

print(
    result["programming_style"]["reason"]
)


print("\nMETRICS")
print("-" * 60)

for key, value in result["metrics"].items():
    print(f"{key:<35}: {value}")


print("\nSTRENGTHS")
print("-" * 60)

for strength in result["strengths"]:
    print("✓", strength)


print("\nWEAKNESSES")
print("-" * 60)

for weakness in result["weaknesses"]:
    print("⚠", weakness)


print("\nRECOMMENDATIONS")
print("-" * 60)

for recommendation in result["recommendations"]:
    print("→", recommendation)


db.close()