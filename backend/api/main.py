import os
import json
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt
from pwdlib import PasswordHash

from backend.database.database import Database
from ml.inference_engine import InferenceEngine


app = FastAPI(
    title="AI Programmer Analyzer API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

JWT_SECRET = os.getenv("JWT_SECRET")

if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET environment variable is not set."
    )

JWT_ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()

security = HTTPBearer()
inference_engine = InferenceEngine()

# =========================================================
# CURRENT USER
# =========================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    try:

        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token."
            )

        return {
            "id": int(user_id),
            "username": payload.get("username")
        }

    except Exception:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token."
        )


@app.get("/auth/me")
def get_me(
    current_user: dict = Depends(get_current_user)
):

    return {
        "user_id": current_user["id"],
        "username": current_user["username"]
    }



# =========================================================
# BEHAVIORAL PROFILE
# =========================================================

def build_behavioral_profile(history):
    """
    Build a behavioral profile from submission history.
    Identifies patterns, habits, and dominant programming styles.
    """
    
    if not history:
        return {
            "patterns": [],
            "behavior_scores": {},
            "strongest_habit": None,
            "weakest_habit": None,
            "summary": "No submission data available."
        }
    
    # Collect all patterns across submissions
    pattern_counts = {}
    behavior_scores = {
        "hash_map_preference": 0.0,
        "set_preference": 0.0,
        "recursion_tendency": 0.0,
        "nested_loop_tendency": 0.0,
        "brute_force_tendency": 0.0
    }
    
    for submission in history:
        # Parse patterns
        try:
            patterns = json.loads(
                submission["patterns"] or "[]"
            )
        except (TypeError, ValueError):
            patterns = []
        
        for pattern in patterns:
            if isinstance(pattern, dict):
                pattern_name = (
                    pattern.get("pattern")
                    or pattern.get("name")
                    or pattern.get("type")
                )
            else:
                pattern_name = str(pattern)
            
            if not pattern_name:
                continue
            
            if pattern_name not in pattern_counts:
                pattern_counts[pattern_name] = 1
            else:
                pattern_counts[pattern_name] += 1
        
        # Accumulate behavior scores
        # -------------------------
        # DATA STRUCTURES
        # -------------------------
        try:
            data_structures = json.loads(
                submission["data_structures"] or "{}"
            )
        except (TypeError, ValueError):
            data_structures = {}
        
        if isinstance(data_structures, dict):
            # Support different possible structures
            dict_usage = (
                data_structures.get("dict")
                or data_structures.get("dictionary")
                or data_structures.get("hash_map")
                or data_structures.get("dict_usage")
                or 0
            )
            set_usage = (
                data_structures.get("set")
                or data_structures.get("set_usage")
                or 0
            )
        else:
            dict_usage = 0
            set_usage = 0
        
        if dict_usage:
            behavior_scores["hash_map_preference"] += 100
        
        if set_usage:
            behavior_scores["set_preference"] += 100
        
        # -------------------------
        # RECURSION
        # -------------------------
        if (submission["recursive_functions"] or 0) > 0:
            behavior_scores["recursion_tendency"] += 100
        
        # -------------------------
        # NESTED LOOPS
        # -------------------------
        if (submission["nested_loops"] or 0) > 0:
            behavior_scores["nested_loop_tendency"] += 100
        
        # -------------------------
        # BRUTE FORCE
        # -------------------------
        brute_force = submission["brute_force_tendency"]
        if brute_force is not None:
            behavior_scores["brute_force_tendency"] += float(
                brute_force
            )
    
    count = len(history)
    
    # Average behavior scores
    for key in behavior_scores:
        behavior_scores[key] = round(
            behavior_scores[key] / count,
            2
        ) if count > 0 else 0.0
    
    # Build recurring patterns list
    recurring_patterns = []
    for pattern, occurrences in sorted(
        pattern_counts.items(),
        key=lambda x: x[1],
        reverse=True
    ):
        percentage = (occurrences / count) * 100.0
        recurring_patterns.append({
            "pattern": pattern,
            "occurrences": occurrences,
            "percentage": round(percentage, 1)
        })
    
    # =========================================================
    # HABIT CLASSIFICATION
    # =========================================================
    
    habit_names = {
        "hash_map_preference": "Hash-map usage",
        "set_preference": "Set usage",
        "recursion_tendency": "Recursion",
        "nested_loop_tendency": "Nested-loop tendency",
        "brute_force_tendency": "Brute-force tendency"
    }
    
    
    # =========================================================
    # STRONGEST HABIT
    # =========================================================
    
    strongest_name = max(
        behavior_scores,
        key=behavior_scores.get
    )
    
    strongest_value = behavior_scores[
        strongest_name
    ]
    
    strongest_habit = {
        "name": habit_names.get(
            strongest_name,
            "Unknown"
        ),
        "score": round(
            strongest_value,
            1
        )
    }
    
    
    # =========================================================
    # IMPROVEMENT AREA
    # =========================================================
    #
    # Low usage does NOT automatically mean weakness.
    #
    # Nested loops and brute force are treated as
    # potentially problematic behaviors.
    #
    # Recursion, hash maps and sets are treated as
    # neutral/positive techniques and therefore should
    # not automatically become weaknesses just because
    # their usage is low.
    # =========================================================
    
    problematic_habits = {
    
        "nested_loop_tendency":
            behavior_scores.get(
                "nested_loop_tendency",
                0
            ),
    
        "brute_force_tendency":
            behavior_scores.get(
                "brute_force_tendency",
                0
            )
    }
    
    
    if problematic_habits:
    
        improvement_name = max(
            problematic_habits,
            key=problematic_habits.get
        )
    
        improvement_value = problematic_habits[
            improvement_name
        ]
    
    else:
    
        improvement_name = None
        improvement_value = 0
    
    
    # Only report an actual improvement area
    # when the behavior is significant.
    
    if improvement_value >= 40:
    
        weakest_habit = {
            "name": habit_names.get(
                improvement_name,
                "Unknown"
            ),
            "score": round(
                improvement_value,
                1
            )
        }
    
    else:
    
        weakest_habit = {
            "name": "No major concern",
            "score": 0.0
        }
    
    # =========================================================
    # BEHAVIOR SUMMARY
    # =========================================================
    
    if (
        strongest_value >= 70
        and improvement_value >= 60
    ):
    
        summary = (
            f"You show a strong preference for "
            f"{habit_names[strongest_name].lower()}, "
            f"while also showing a noticeable tendency "
            f"toward {habit_names[improvement_name].lower()}."
        )
    
    elif strongest_value >= 70:
    
        summary = (
            f"You show a strong preference for "
            f"{habit_names[strongest_name].lower()}, "
            f"appearing in roughly "
            f"{strongest_value:.0f}% of your analyzed submissions."
        )
    
    elif improvement_value >= 60:
    
        summary = (
            f"Your programming style is relatively varied, "
            f"but {habit_names[improvement_name].lower()} "
            f"appears frequently enough to be worth reviewing."
        )
    
    elif recurring_patterns:
    
        summary = (
            "Your submissions show recurring algorithmic "
            "patterns, but your approach is not dominated "
            "by a single technique."
        )
    
    else:
    
        summary = (
            "Your programming behavior is still diverse. "
            "More submissions will make recurring habits "
            "easier to identify."
        )
    
    return {
        "patterns": recurring_patterns,
        "behavior_scores": behavior_scores,
        "strongest_habit": strongest_habit,
        "weakest_habit": weakest_habit,
        "summary": summary
    }


# =========================================================
# RECURRING PATTERN INSIGHTS
# =========================================================

def build_pattern_insights(
    behavioral_profile,
    history
):
    patterns = behavioral_profile.get(
        "patterns",
        []
    )

    if not patterns:
        return []


    insights = []


    for pattern in patterns[:5]:

        name = pattern.get(
            "pattern",
            "unknown"
        )

        occurrences = int(
            pattern.get(
                "occurrences",
                0
            )
        )

        percentage = float(
            pattern.get(
                "percentage",
                0
            )
        )


        readable_name = (
            name
            .replace("_", " ")
            .title()
        )


        # -------------------------------------------------
        # Classify pattern
        # -------------------------------------------------

        if (
            "brute" in name.lower()
            or "linear_search" in name.lower()
        ):

            category = "search"

        elif (
            "hash" in name.lower()
            or "dict" in name.lower()
        ):

            category = "data_structure"

        elif (
            "recursion" in name.lower()
            or "recursive" in name.lower()
        ):

            category = "recursion"

        elif (
            "loop" in name.lower()
        ):

            category = "iteration"

        else:

            category = "algorithm"


        # -------------------------------------------------
        # Generate interpretation
        # -------------------------------------------------

        if percentage >= 60:

            message = (
                f"{readable_name} appears in "
                f"{occurrences} of your "
                f"{len(history)} analyzed submissions. "
                f"This is a highly recurring technique "
                f"in your current programming style."
            )

        elif percentage >= 30:

            message = (
                f"{readable_name} appears in "
                f"{occurrences} of your "
                f"{len(history)} analyzed submissions. "
                f"This is a recurring part of your "
                f"problem-solving approach."
            )

        else:

            message = (
                f"{readable_name} appears in "
                f"{occurrences} of your "
                f"{len(history)} analyzed submissions."
            )


        insights.append({
            "pattern": name,
            "name": readable_name,
            "occurrences": occurrences,
            "percentage": round(
                percentage,
                1
            ),
            "category": category,
            "message": message
        })


    return insights


# =========================================================
# GROWTH ANALYSIS
# =========================================================

def build_growth_analysis(history):

    if len(history) < 2:
        return {
            "status": "insufficient_data",
            "message": (
                "Analyze more submissions to measure "
                "your programming growth."
            ),
            "quality_change": 0,
            "optimization_change": 0,
            "complexity_change": 0,
            "quality_direction": "stable",
            "optimization_direction": "stable",
            "complexity_direction": "stable"
        }


    # -----------------------------------------------------
    # Split history into earlier and recent submissions
    # -----------------------------------------------------

    midpoint = max(
        1,
        len(history) // 2
    )

    earlier = history[:midpoint]
    recent = history[midpoint:]


    # -----------------------------------------------------
    # Helpers
    # -----------------------------------------------------

    def average(values):

        values = [
            float(value or 0)
            for value in values
        ]

        return (
            sum(values) / len(values)
            if values
            else 0.0
        )


    # -----------------------------------------------------
    # Earlier metrics
    # -----------------------------------------------------

    earlier_quality = average([
        item["code_quality_score"]
        if item["code_quality_score"] is not None
        else item["maintainability_index"]
        for item in earlier
    ])


    earlier_optimization = average([
        item["optimization_score"]
        if item["optimization_score"] is not None
        else max(
            0.0,
            min(
                100.0,
                100 -
                (
                    float(
                        item["cyclomatic_complexity"]
                        or 0
                    ) * 6
                )
            )
        )
        for item in earlier
    ])


    earlier_complexity = average([
        item["cyclomatic_complexity"]
        for item in earlier
    ])


    # -----------------------------------------------------
    # Recent metrics
    # -----------------------------------------------------

    recent_quality = average([
        item["code_quality_score"]
        if item["code_quality_score"] is not None
        else item["maintainability_index"]
        for item in recent
    ])


    recent_optimization = average([
        item["optimization_score"]
        if item["optimization_score"] is not None
        else max(
            0.0,
            min(
                100.0,
                100 -
                (
                    float(
                        item["cyclomatic_complexity"]
                        or 0
                    ) * 6
                )
            )
        )
        for item in recent
    ])


    recent_complexity = average([
        item["cyclomatic_complexity"]
        for item in recent
    ])


    # -----------------------------------------------------
    # Calculate changes
    # -----------------------------------------------------

    quality_change = (
        recent_quality -
        earlier_quality
    )


    optimization_change = (
        recent_optimization -
        earlier_optimization
    )


    complexity_change = (
        recent_complexity -
        earlier_complexity
    )


    # -----------------------------------------------------
    # Direction helper
    # -----------------------------------------------------

    def direction(value):

        if value > 3:
            return "improving"

        if value < -3:
            return "declining"

        return "stable"


    quality_direction = direction(
        quality_change
    )


    optimization_direction = direction(
        optimization_change
    )


    # Complexity is reversed:
    # decreasing complexity = improvement.

    if complexity_change < -0.5:

        complexity_direction = "improving"

    elif complexity_change > 0.5:

        complexity_direction = "declining"

    else:

        complexity_direction = "stable"


    # -----------------------------------------------------
    # Overall growth
    # -----------------------------------------------------

    improving_metrics = 0
    declining_metrics = 0


    if quality_direction == "improving":
        improving_metrics += 1

    elif quality_direction == "declining":
        declining_metrics += 1


    if optimization_direction == "improving":
        improving_metrics += 1

    elif optimization_direction == "declining":
        declining_metrics += 1


    if complexity_direction == "improving":
        improving_metrics += 1

    elif complexity_direction == "declining":
        declining_metrics += 1


    # =========================================================
    # OVERALL GROWTH CLASSIFICATION
    # =========================================================

    if (
        quality_direction == "declining"
        and quality_change <= -10
    ):

        overall = "needs_attention"

        message = (
            f"Your recent code quality has dropped by "
            f"{abs(quality_change):.1f} points compared "
            "with your earlier submissions. Your complexity "
            "has improved, so focus on maintaining that "
            "efficiency while restoring code quality and "
            "readability."
        )

    elif (
        improving_metrics >= 2
        and declining_metrics == 0
    ):

        overall = "improving"

        message = (
            "Your recent submissions show measurable "
            "improvement across multiple programming metrics."
        )

    elif (
        declining_metrics >= 2
    ):

        overall = "declining"

        message = (
            "Several recent metrics have declined compared "
            "with your earlier submissions. Reviewing your "
            "latest solutions may reveal where your approach "
            "changed."
        )

    elif (
        improving_metrics > declining_metrics
    ):

        overall = "slightly_improving"

        message = (
            "Your overall programming profile is moving "
            "in a positive direction, although some metrics "
            "are still fluctuating."
        )

    elif (
        declining_metrics > improving_metrics
    ):

        overall = "slightly_declining"

        message = (
            "Some recent programming metrics have declined. "
            "Consider reviewing your latest solutions while "
            "continuing to build on areas that are improving."
        )

    else:

        overall = "stable"

        message = (
            "Your programming metrics are relatively stable. "
            "Trying different approaches may help create "
            "measurable improvements."
        )


    return {

        "status": "available",

        "overall": overall,

        "message": message,

        "quality_change": round(
            quality_change,
            2
        ),

        "optimization_change": round(
            optimization_change,
            2
        ),

        "complexity_change": round(
            complexity_change,
            2
        ),

        "quality_direction":
            quality_direction,

        "optimization_direction":
            optimization_direction,

        "complexity_direction":
            complexity_direction,

        "earlier": {
            "quality": round(
                earlier_quality,
                2
            ),
            "optimization": round(
                earlier_optimization,
                2
            ),
            "complexity": round(
                earlier_complexity,
                2
            )
        },

        "recent": {
            "quality": round(
                recent_quality,
                2
            ),
            "optimization": round(
                recent_optimization,
                2
            ),
            "complexity": round(
                recent_complexity,
                2
            )
        }
    }


# =========================================================
# MY PROFILE
# =========================================================

@app.get("/profile/me")
def get_my_profile(
    current_user: dict = Depends(get_current_user)
):
    db = Database(
        "data/ml_dataset_v2.db"
    )

    try:
        user_id = current_user["id"]
        history = db.get_user_submissions(
            user_id
        )

        if not history:
            return {
                "user_id": user_id,
                "username": current_user["username"],
                "submissions": 0,
                "average_complexity": 0,
                "code_quality_score": 0,
                "optimization_score": 0,
                "algorithm_diversity": 0,
                "data_structure_diversity": 0,
                "problem_solving_diversity": 0,
                "cluster": None,
                "cluster_distribution": {},
                "recent_submissions": [],
                "trend": [],
                "ai_insights": {
                    "strength": "Start analyzing code to unlock your first programming insights.",
                    "weakness": "No submission history yet, so there isn't enough data for a meaningful assessment.",
                    "complexity": "Continue building more submissions to track your coding patterns over time.",
                    "recommendation": "Submit a few solutions to generate your first AI profile and improvement suggestions.",
                    "progress": "Your profile will become more accurate as you analyze more code."
                }
            }

        complexity_values = []
        quality_values = []
        optimization_values = []
        algorithm_values = []
        data_structure_values = []
        problem_values = []
        cluster_counts = {}
        recent_submissions = []

        for submission in history:
            try:
                patterns = json.loads(
                    submission["patterns"] or "[]"
                )
            except (TypeError, ValueError):
                patterns = []

            try:
                data_structures = json.loads(
                    submission["data_structures"] or "{}"
                )
            except (TypeError, ValueError):
                data_structures = {}

            complexity_value = float(
                submission["cyclomatic_complexity"] or 0
            )
            quality_value = float(
                submission["code_quality_score"] or submission["maintainability_index"] or 0
            )
            optimization_value = float(
                submission["optimization_score"] or max(0.0, min(100.0, 100 - (complexity_value * 6)))
            )
            algorithm_value = float(
                submission["algorithm_diversity"] or min(100.0, len(patterns) * 20.0)
            )
            data_structure_value = float(
                submission["data_structure_diversity"] or min(100.0, len(data_structures) * 25.0)
            )
            problem_value = float(
                submission["problem_solving_diversity"] or min(
                    100.0,
                    ((submission["recursive_functions"] or 0) * 35)
                    + ((submission["num_functions"] or 0) * 4)
                    + ((submission["if_statements"] or 0) * 1.5)
                )
            )

            cluster = submission["cluster"]
            if cluster is not None:
                cluster_counts[cluster] = cluster_counts.get(cluster, 0) + 1

            complexity_values.append(complexity_value)
            quality_values.append(quality_value)
            optimization_values.append(optimization_value)
            algorithm_values.append(algorithm_value)
            data_structure_values.append(data_structure_value)
            problem_values.append(problem_value)

            recent_submissions.append({
                "id": submission["id"],
                "problem_name": submission["problem_name"],
                "submitted_at": submission["submitted_at"],
                "cluster": cluster,
                "complexity": round(complexity_value, 2),
                "quality_score": round(quality_value, 2),
                "optimization_score": round(optimization_value, 2)
            })

        count = len(history)
        behavioral_profile = build_behavioral_profile(
            history
        )
        pattern_insights = build_pattern_insights(
            behavioral_profile,
            history
        )
        growth_analysis = build_growth_analysis(
            history
        )
        current_cluster = None
        if cluster_counts:
            current_cluster = max(
                cluster_counts.items(),
                key=lambda item: item[1]
            )[0]

        # =====================================================
        # PERFORMANCE TREND
        # =====================================================
        trend = []
        for entry in history[-5:]:
            complexity = float(
                entry["cyclomatic_complexity"] or 0
            )
            quality = entry["code_quality_score"]
            optimization = entry["optimization_score"]

            # Fallback for older submissions
            if quality is None:
                quality = max(
                    0.0,
                    min(
                        100.0,
                        float(
                            entry["maintainability_index"] or 0
                        )
                    )
                )

            if optimization is None:
                optimization = max(
                    0.0,
                    min(
                        100.0,
                        100 - (complexity * 6)
                    )
                )

            trend.append({
                "id": entry["id"],
                "problem_name": entry["problem_name"] or "Submission",
                "date": entry["submitted_at"],
                "complexity": round(complexity, 2),
                "quality": round(float(quality), 2),
                "optimization": round(float(optimization), 2)
            })

        avg_optimization = (
            sum(optimization_values) / count
        ) if count else 0.0
        avg_algorithm = (
            sum(algorithm_values) / count
        ) if count else 0.0
        avg_problem = (
            sum(problem_values) / count
        ) if count else 0.0
        avg_quality = (
            sum(quality_values) / count
        ) if count else 0.0
        avg_complexity = (
            sum(complexity_values) / count
        ) if count else 0.0

        if avg_optimization >= 75:
            strength = "You consistently choose solutions that balance correctness with efficiency."
        elif avg_algorithm >= 50:
            strength = "You are exploring varied algorithmic patterns and problem-solving strategies."
        else:
            strength = "You are building a strong foundation and can improve by comparing multiple solution approaches."

        if avg_optimization < 60:
            weakness = "Your solutions may be spending more time or effort than necessary on simpler problems."
        elif avg_algorithm < 40:
            weakness = "You may be relying too heavily on a narrow set of patterns or techniques."
        elif avg_problem < 40:
            weakness = "Your problem-solving strategy may be too solution-first and not strategy-first."
        else:
            weakness = "You are close to strong programming habits, but there is still room to deepen your algorithmic thinking."

        if avg_complexity > 20:
            complexity_insight = "Your code tends to be more complex than average, which may reduce readability and maintainability."
        elif avg_complexity > 10:
            complexity_insight = "Your complexity is moderate; a cleaner decomposition could improve readability."
        else:
            complexity_insight = "Your solutions are staying relatively lean and manageable."

        # =========================================================
        # PERSONALIZED AI RECOMMENDATION
        # =========================================================

        _behavior_scores = behavioral_profile.get(
            "behavior_scores",
            {}
        )

        _recurring_patterns = behavioral_profile.get(
            "patterns",
            []
        )


        hash_map_score = float(
            _behavior_scores.get(
                "hash_map_preference",
                0
            )
        )

        set_score = float(
            _behavior_scores.get(
                "set_preference",
                0
            )
        )

        recursion_score = float(
            _behavior_scores.get(
                "recursion_tendency",
                0
            )
        )

        nested_loop_score = float(
            _behavior_scores.get(
                "nested_loop_tendency",
                0
            )
        )

        brute_force_score = float(
            _behavior_scores.get(
                "brute_force_tendency",
                0
            )
        )


        # ---------------------------------------------------------
        # Identify recurring techniques
        # ---------------------------------------------------------

        top_patterns = [
            item["pattern"]
            for item in _recurring_patterns[:3]
        ]

        pattern_text = ", ".join(
            pattern.replace("_", " ")
            for pattern in top_patterns
        )


        # ---------------------------------------------------------
        # Priority 1:
        # Inefficient/problematic behavior
        # ---------------------------------------------------------

        if brute_force_score >= 60:

            recommendation = (
                "You show a strong tendency toward brute-force "
                "solutions. Before implementing a direct search, "
                "look for ways to reduce the search space using "
                "hashing, sorting, two pointers, greedy strategies, "
                "or other problem-specific techniques."
            )

        elif nested_loop_score >= 60:

            recommendation = (
                "Nested loops appear frequently in your solutions. "
                "Before adding another loop, consider whether a "
                "hash map, set, sorting strategy, prefix structure, "
                "or two-pointer approach can reduce repeated work."
            )


        # ---------------------------------------------------------
        # Priority 2:
        # Narrow algorithmic repertoire
        # ---------------------------------------------------------

        elif (
            avg_algorithm < 40
            and avg_problem < 40
        ):

            if pattern_text:

                recommendation = (
                    "Your solutions are currently concentrated around "
                    f"a relatively small set of techniques, especially "
                    f"{pattern_text}. Try solving the same problem "
                    "using two or three different strategies before "
                    "choosing your final approach."
                )

            else:

                recommendation = (
                    "Your algorithmic repertoire is still developing. "
                    "Practice solving the same problem using multiple "
                    "strategies such as hashing, two pointers, greedy "
                    "techniques, binary search, or divide-and-conquer."
                )


        # ---------------------------------------------------------
        # Priority 3:
        # Low algorithm diversity
        # ---------------------------------------------------------

        elif avg_algorithm < 40:

            recommendation = (
                "Your solutions tend to rely on a relatively narrow "
                "set of algorithmic patterns. Deliberately practice "
                "different approaches to the same type of problem "
                "to expand your algorithmic toolkit."
            )


        # ---------------------------------------------------------
        # Priority 4:
        # Low problem-solving diversity
        # ---------------------------------------------------------

        elif avg_problem < 40:

            recommendation = (
                "Your implementation skills are developing faster "
                "than your strategy selection. Before coding, spend "
                "more time identifying the problem type, possible "
                "approaches, and trade-offs between them."
            )


        # ---------------------------------------------------------
        # Priority 5:
        # Strong hash-map preference
        # ---------------------------------------------------------

        elif hash_map_score >= 60:

            recommendation = (
                "Hash maps are one of your strongest recurring "
                "techniques. Keep using them when appropriate, but "
                "challenge yourself to recognize when alternatives "
                "such as sorting, sets, binary search, or two pointers "
                "may provide a simpler solution."
            )


        # ---------------------------------------------------------
        # Priority 6:
        # Quality
        # ---------------------------------------------------------

        elif avg_quality < 60:

            recommendation = (
                "Focus on writing cleaner, more maintainable code. "
                "Try simplifying functions, reducing unnecessary "
                "logic, and giving each part of the solution a clear "
                "responsibility."
            )


        # ---------------------------------------------------------
        # Strong overall profile
        # ---------------------------------------------------------

        else:

            recommendation = (
                "Your programming profile is developing well. "
                "Continue challenging yourself with harder problems "
                "and compare multiple solution strategies to keep "
                "expanding your programming toolkit."
            )

        recent = trend[-5:] if trend else []
        quality_improving = False
        optimization_improving = False
        complexity_improving = False

        if len(recent) >= 2:
            first = recent[0]
            last = recent[-1]
            quality_improving = last["quality"] > first["quality"]
            optimization_improving = last["optimization"] > first["optimization"]
            complexity_improving = last["complexity"] < first["complexity"]

        progress = (
            "Keep analyzing more submissions to build a stronger "
            "picture of how your programming behavior evolves over time."
        )

        if avg_optimization >= 75 and quality_improving and optimization_improving:
            progress = (
                "Your recent performance shows strong gains in "
                "code quality and optimization. Your programming "
                "habits appear to be moving in a positive direction."
            )
        elif quality_improving:
            progress = (
                "Your recent code quality is improving. "
                "Your latest solutions appear more maintainable "
                "than your earlier submissions."
            )
        elif optimization_improving:
            progress = (
                "Your recent optimization scores are improving, "
                "suggesting that your algorithmic choices are becoming "
                "more efficient."
            )
        elif complexity_improving:
            progress = (
                "Your recent solutions are becoming less complex. "
                "That is a positive sign for readability and maintainability."
            )
        elif (
            not quality_improving
            and not optimization_improving
            and len(recent) >= 3
        ):
            progress = (
                "Your recent metrics are relatively stable. "
                "Trying different algorithms or deliberately optimizing "
                "your next few solutions could reveal new areas of growth."
            )
        else:
            progress = (
                "Your programming profile is still developing. "
                "Continue analyzing different types of problems to "
                "build a clearer behavioral pattern."
            )

        # -----------------------------------------------------
        # AI INSIGHTS OBJECT
        # -----------------------------------------------------
        ai_insights = {
            "strength": strength,
            "weakness": weakness,
            "complexity": complexity_insight,
            "recommendation": recommendation,
            "progress": progress
        }

        return {
            "user_id": user_id,
            "username": current_user["username"],
            "submissions": count,
            "average_complexity": round(
                sum(complexity_values) / count,
                2
            ),
            "code_quality_score": round(
                sum(quality_values) / count,
                2
            ),
            "optimization_score": round(
                sum(optimization_values) / count,
                2
            ),
            "algorithm_diversity": round(
                sum(algorithm_values) / count,
                2
            ),
            "data_structure_diversity": round(
                sum(data_structure_values) / count,
                2
            ),
            "problem_solving_diversity": round(
                sum(problem_values) / count,
                2
            ),
            "cluster": current_cluster,
            "cluster_distribution": cluster_counts,
            "recent_submissions": recent_submissions[-5:],
            "trend": trend,
            "ai_insights": ai_insights,
            "behavioral_profile": behavioral_profile,
            "pattern_insights": pattern_insights,
            "growth_analysis": growth_analysis
        }
    finally:
        db.close()


# =========================================================
# MY SUBMISSION HISTORY
# =========================================================

@app.get("/history/me")
def get_my_history(
    current_user: dict = Depends(get_current_user)
):

    db = Database(
        "data/ml_dataset_v2.db"
    )

    try:

        history = db.get_user_submissions(
            current_user["id"]
        )

        submissions = []

        for submission in history:
            submissions.append({
                "id": submission["id"],
                "problem_name": submission["problem_name"],
                "language": submission["language"],
                "submitted_at": submission["submitted_at"],
                # -------------------------
                # COUNTS
                # -------------------------
                "loc": submission["loc"] or 0,
                "blank_lines": submission["blank_lines"] or 0,
                "comment_lines": submission["comment_lines"] or 0,
                "num_functions": submission["num_functions"] or 0,
                "num_classes": submission["num_classes"] or 0,
                "num_imports": submission["num_imports"] or 0,
                "num_variables": submission["num_variables"] or 0,
                "num_constants": submission["num_constants"] or 0,
                "if_statements": submission["if_statements"] or 0,
                "for_loops": submission["for_loops"] or 0,
                "while_loops": submission["while_loops"] or 0,
                "total_loops": submission["total_loops"] or 0,
                "nested_loops": submission["nested_loops"] or 0,
                "max_loop_nesting_depth": submission["max_loop_nesting_depth"] or 0,
                "recursive_functions": submission["recursive_functions"] or 0,
                # -------------------------
                # COMPLEXITY
                # -------------------------
                "cyclomatic_complexity": submission["cyclomatic_complexity"] or 0,
                "maximum_cyclomatic_complexity": submission["maximum_cyclomatic_complexity"] or 0,
                "maintainability_index": submission["maintainability_index"] or 0,
                # -------------------------
                # FUNCTIONS
                # -------------------------
                "avg_function_length": submission["avg_function_length"] or 0,
                "max_function_length": submission["max_function_length"] or 0,
                "avg_function_args": submission["avg_function_args"] or 0,
                "total_return_statements": submission["total_return_statements"] or 0,
                # -------------------------
                # PATTERNS
                # -------------------------
                "patterns": submission["patterns"] or "[]",
                "data_structures": submission["data_structures"] or "{}",
                # -------------------------
                # ML RESULTS
                # -------------------------
                "cluster": submission["cluster"],
                "cluster_memberships": submission["cluster_memberships"] or "[]",
                "optimization_score": submission["optimization_score"] or 0,
                "code_quality_score": submission["code_quality_score"] or 0,
                "algorithm_diversity": submission["algorithm_diversity"] or 0,
                "data_structure_diversity": submission["data_structure_diversity"] or 0,
                "problem_solving_diversity": submission["problem_solving_diversity"] or 0,
                "brute_force_tendency": submission["brute_force_tendency"] or 0,
                "nested_loop_percentage": submission["nested_loop_percentage"] or 0,
                "recursion_percentage": submission["recursion_percentage"] or 0,
                "improvement_score": submission["improvement_score"] or 0
            })

        return {
            "user_id": current_user["id"],
            "username": current_user["username"],
            "submissions": submissions
        }

    finally:
        db.close()


@app.get("/submissions/{submission_id}")
def get_submission(
    submission_id: int,
    current_user: dict = Depends(get_current_user)
):
    db = Database(
        "data/ml_dataset_v2.db"
    )

    try:
        cursor = db.connection.cursor()

        cursor.execute(
            """
            SELECT
                submissions.*,
                code_features.*
            FROM submissions

            LEFT JOIN code_features
                ON submissions.id = code_features.submission_id

            WHERE submissions.id = ?
              AND submissions.user_id = ?
            """,
            (submission_id, current_user["id"])
        )

        submission = cursor.fetchone()

        if submission is None:
            raise HTTPException(
                status_code=404,
                detail="Submission not found."
            )

        explanation = build_submission_explanation(submission)

        return {
            "id": submission["id"],
            "user_id": submission["user_id"],
            "problem_name": submission["problem_name"],
            "language": submission["language"],
            "code": submission["code"],
            "submitted_at": submission["submitted_at"],
            "loc": submission["loc"] or 0,
            "blank_lines": submission["blank_lines"] or 0,
            "comment_lines": submission["comment_lines"] or 0,
            "num_functions": submission["num_functions"] or 0,
            "num_classes": submission["num_classes"] or 0,
            "num_imports": submission["num_imports"] or 0,
            "num_variables": submission["num_variables"] or 0,
            "num_constants": submission["num_constants"] or 0,
            "if_statements": submission["if_statements"] or 0,
            "for_loops": submission["for_loops"] or 0,
            "while_loops": submission["while_loops"] or 0,
            "total_loops": submission["total_loops"] or 0,
            "nested_loops": submission["nested_loops"] or 0,
            "max_loop_nesting_depth": submission["max_loop_nesting_depth"] or 0,
            "recursive_functions": submission["recursive_functions"] or 0,
            "cyclomatic_complexity": submission["cyclomatic_complexity"] or 0,
            "maximum_cyclomatic_complexity": submission["maximum_cyclomatic_complexity"] or 0,
            "maintainability_index": submission["maintainability_index"] or 0,
            "patterns": submission["patterns"] or "[]",
            "data_structures": submission["data_structures"] or "{}",
            "cluster": submission["cluster"],
            "cluster_memberships": submission["cluster_memberships"] or "[]",
            "optimization_score": submission["optimization_score"] or 0,
            "code_quality_score": submission["code_quality_score"] or 0,
            "algorithm_diversity": submission["algorithm_diversity"] or 0,
            "data_structure_diversity": submission["data_structure_diversity"] or 0,
            "problem_solving_diversity": submission["problem_solving_diversity"] or 0,
            "brute_force_tendency": submission["brute_force_tendency"] or 0,
            "nested_loop_percentage": submission["nested_loop_percentage"] or 0,
            "recursion_percentage": submission["recursion_percentage"] or 0,
            "improvement_score": submission["improvement_score"] or 0,
            "explanation": explanation
        }
    finally:
        db.close()


class AnalyzeRequest(BaseModel):
    code: str
    problem_name: str = "Untitled Problem"


# =========================================================
# ANALYZE CODE
# =========================================================

@app.post("/submissions/analyze")
def analyze_submission(
    request: AnalyzeRequest,
    current_user: dict = Depends(get_current_user)
):
    if not request.code.strip():
        raise HTTPException(
            status_code=400,
            detail="Code cannot be empty."
        )

    analysis = inference_engine.analyze_code(
        request.code
    )

    if not analysis["valid"]:
        raise HTTPException(
            status_code=400,
            detail=analysis["error"]
        )

    prediction = inference_engine.predict(
        analysis
    )

    db = Database(
        "data/ml_dataset_v2.db"
    )

    try:
        user_id = current_user["id"]
        submission_id = db.save_submission(
            user_id=user_id,
            problem_name=request.problem_name,
            language="Python",
            code=request.code
        )

        db.save_features(
            submission_id=submission_id,
            features=analysis["ast"],
            complexity=analysis["complexity"],
            ml_results=analysis["features"] | {
                "cluster": prediction["cluster"],
                "cluster_memberships":
                    prediction["memberships"].tolist()
            }
        )

        return {
            "message": "Code analyzed successfully.",
            "submission_id": submission_id,
            "user_id": user_id,
            "username": current_user["username"],
            "problem_name": request.problem_name,
            "cluster": prediction["cluster"],
            "cluster_memberships": (
                prediction["memberships"].tolist()
            ),
            "features": analysis["features"]
        }
    finally:
        db.close()


# =========================================================
# REQUEST MODELS
# =========================================================

class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "status": "online",
        "message": "AI Programmer Analyzer API"
    }


# =========================================================
# REGISTER
# =========================================================

@app.post("/auth/register")
def register(
    request: RegisterRequest
):

    username = request.username.strip()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Username cannot be empty."
        )

    if len(username) < 3:
        raise HTTPException(
            status_code=400,
            detail="Username must contain at least 3 characters."
        )

    if len(request.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters."
        )

    db = Database(
        "data/ml_dataset_v2.db"
    )

    try:

        existing_user = db.get_user(
            username
        )

        if existing_user:

            raise HTTPException(
                status_code=409,
                detail="Username already exists."
            )

        hashed_password = password_hash.hash(
            request.password
        )

        user_id = db.create_user(
            username
        )

        cursor = db.connection.cursor()

        cursor.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
            """,
            (
                hashed_password,
                user_id
            )
        )

        db.connection.commit()

        return {
            "message": "Registration successful.",
            "user_id": user_id,
            "username": username
        }

    finally:

        db.close()


# =========================================================
# LOGIN
# =========================================================

@app.post("/auth/login")
def login(
    request: LoginRequest
):

    username = request.username.strip()

    db = Database(
        "data/ml_dataset_v2.db"
    )

    try:

        user = db.get_user(
            username
        )

        if not user:

            raise HTTPException(
                status_code=401,
                detail="Invalid username or password."
            )

        stored_password_hash = user["password_hash"]

        # Existing seed users don't have passwords yet.
        if not stored_password_hash:

            raise HTTPException(
                status_code=401,
                detail="This account has no login password."
            )

        if not password_hash.verify(
            request.password,
            stored_password_hash
        ):

            raise HTTPException(
                status_code=401,
                detail="Invalid username or password."
            )

        token = jwt.encode(
            {
                "sub": str(user["id"]),
                "username": user["username"]
            },
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user["id"],
            "username": user["username"]
        }

    finally:

        db.close()
def build_submission_explanation(submission):
    """
    Generate deterministic, explainable insights from
    the features already stored for a submission.
    """

    complexity = float(
        submission["cyclomatic_complexity"] or 0
    )

    maintainability = float(
        submission["maintainability_index"] or 0
    )

    optimization = submission["optimization_score"]

    if optimization is None:
        optimization = max(
            0.0,
            min(100.0, 100 - (complexity * 6))
        )
    else:
        optimization = float(optimization)

    quality = submission["code_quality_score"]

    if quality is None:
        quality = maintainability
    else:
        quality = float(quality)

    patterns = []

    try:
        patterns = json.loads(
            submission["patterns"] or "[]"
        )
    except (TypeError, ValueError):
        patterns = []

    data_structures = {}

    try:
        data_structures = json.loads(
            submission["data_structures"] or "{}"
        )
    except (TypeError, ValueError):
        data_structures = {}


    # =====================================================
    # DETECTED APPROACH
    # =====================================================

    detected = []

    for pattern in patterns:

        if isinstance(pattern, dict):

            name = pattern.get("pattern")

            if name:
                detected.append(
                    name.replace("_", " ").title()
                )

    if not detected:

        if data_structures.get("dict_usage", 0) > 0:
            detected.append("Dictionary-based approach")

        if data_structures.get("set_usage", 0) > 0:
            detected.append("Set-based approach")

        if (
            submission["for_loops"] or 0
        ) > 0 and (
            submission["nested_loops"] or 0
        ) == 0:

            detected.append("Linear iteration")

    if not detected:
        detected.append("General algorithmic approach")


    # =====================================================
    # COMPLEXITY EXPLANATION
    # =====================================================

    if complexity <= 5:

        complexity_explanation = (
            f"The solution has a cyclomatic complexity of "
            f"{complexity:.1f}, indicating relatively simple "
            f"control flow with limited branching."
        )

    elif complexity <= 10:

        complexity_explanation = (
            f"The solution has a cyclomatic complexity of "
            f"{complexity:.1f}. The control flow is moderate, "
            f"so simplifying conditions or splitting logic "
            f"could improve readability."
        )

    else:

        complexity_explanation = (
            f"The solution has a cyclomatic complexity of "
            f"{complexity:.1f}, indicating relatively complex "
            f"control flow. Breaking the logic into smaller "
            f"functions could make it easier to maintain."
        )


    # =====================================================
    # OPTIMIZATION EXPLANATION
    # =====================================================

    if optimization >= 80:

        optimization_explanation = (
            f"The optimization score is {optimization:.1f}. "
            f"The detected structure suggests that the solution "
            f"avoids substantial unnecessary work."
        )

    elif optimization >= 60:

        optimization_explanation = (
            f"The optimization score is {optimization:.1f}. "
            f"The solution is reasonably efficient, but there "
            f"may still be opportunities to reduce operations."
        )

    else:

        optimization_explanation = (
            f"The optimization score is {optimization:.1f}. "
            f"Consider whether a different algorithm or data "
            f"structure could reduce repeated work."
        )


    # =====================================================
    # QUALITY EXPLANATION
    # =====================================================

    if quality >= 80:

        quality_explanation = (
            f"The code quality score is {quality:.1f}. "
            f"The implementation appears relatively maintainable."
        )

    elif quality >= 60:

        quality_explanation = (
            f"The code quality score is {quality:.1f}. "
            f"The implementation is reasonably maintainable, "
            f"although there is room for cleaner structure."
        )

    else:

        quality_explanation = (
            f"The code quality score is {quality:.1f}. "
            f"Consider improving structure, naming, and "
            f"function decomposition."
        )


    # =====================================================
    # IMPROVEMENT
    # =====================================================

    if optimization < 60:

        improvement = (
            "Look for a more efficient algorithm or data "
            "structure before optimizing the implementation."
        )

    elif complexity > 10:

        improvement = (
            "Reduce control-flow complexity by simplifying "
            "conditions and extracting reusable logic."
        )

    elif quality < 60:

        improvement = (
            "Improve readability with clearer naming and "
            "smaller, more focused functions."
        )

    else:

        improvement = (
            "The solution is already in a good range. "
            "Focus on edge cases and compare it with alternative "
            "approaches to find further improvements."
        )


    # =====================================================
    # RETURN
    # =====================================================

    return {
        "detected_approaches": detected,
        "complexity": {
            "score": round(complexity, 2),
            "explanation": complexity_explanation
        },
        "optimization": {
            "score": round(optimization, 2),
            "explanation": optimization_explanation
        },
        "quality": {
            "score": round(quality, 2),
            "explanation": quality_explanation
        },
        "improvement": improvement
    }