import sqlite3
from pathlib import Path

import numpy as np
import streamlit as st

from backend.analyzer.behavior import BehaviorAnalyzer
from backend.database.database import Database

from ml.feature_builder import MLFeatureBuilder
from ml.inference_engine import InferenceEngine


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Programmer Analyzer",
    page_icon="🧠",
    layout="wide"
)


# =========================================================
# DATABASE
# =========================================================

DB_PATH = Path("data/ml_dataset_v2.db")


@st.cache_resource
def get_connection():

    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    return connection


db = get_connection()


# =========================================================
# DATABASE HELPERS
# =========================================================

@st.cache_data
def get_dashboard_stats():

    cursor = db.cursor()

    # Total programmers
    cursor.execute(
        "SELECT COUNT(*) AS count FROM users"
    )

    programmers = cursor.fetchone()["count"]

    # Total submissions
    cursor.execute(
        "SELECT COUNT(*) AS count FROM submissions"
    )

    submissions = cursor.fetchone()["count"]

    # Average complexity + maintainability
    cursor.execute("""
        SELECT
            AVG(cyclomatic_complexity) AS avg_complexity,
            AVG(maintainability_index) AS avg_maintainability
        FROM code_features
    """)

    row = cursor.fetchone()

    avg_complexity = row["avg_complexity"] or 0
    avg_maintainability = (
        row["avg_maintainability"] or 0
    )

    return {
        "programmers": programmers,
        "submissions": submissions,
        "avg_complexity": avg_complexity,
        "avg_maintainability": avg_maintainability
    }


stats = get_dashboard_stats()


# =========================================================
# ML MODEL
# =========================================================

PROFILE_NAMES = {
    0: "Recursive Algorithmist",
    1: "Optimization Specialist",
    2: "Brute Force Specialist",
    3: "Algorithm Explorer",
    4: "Clean Code Specialist"
}

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

inference_engine = InferenceEngine()


def get_programmer_ml_profile(
    features
):

    return inference_engine.predict_features(
        features
    )


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🧠 AI Programmer Analyzer")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Analyze Code",
        "Programmer Profile",
        "History"
    ]
)


# =========================================================
# HEADER
# =========================================================

st.title("🧠 AI Programmer Analyzer")

st.markdown(
    "### Understand how you program."
)

st.caption(
    "Analyze code, discover programming patterns, "
    "and use machine learning to understand "
    "programming behavior."
)


# =========================================================
# DASHBOARD
# =========================================================

# =========================================================
# DASHBOARD
# =========================================================

if page == "Dashboard":

    st.header("📊 Dashboard")

    st.write(
        "Your programming behavior at a glance."
    )

    # -----------------------------------------------------
    # KEY METRICS
    # -----------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "👨‍💻 Programmers",
            stats["programmers"]
        )

    with col2:

        st.metric(
            "📝 Submissions",
            stats["submissions"]
        )

    with col3:

        st.metric(
            "⚙️ Avg Complexity",
            f"{stats['avg_complexity']:.2f}"
        )

    with col4:

        st.metric(
            "🧹 Avg Maintainability",
            f"{stats['avg_maintainability']:.2f}"
        )

    st.divider()

    # -----------------------------------------------------
    # AI ENGINE STATUS
    # -----------------------------------------------------

    st.subheader(
        "🧠 AI Analysis Engine"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.info(
            f"""
            **ML Dataset**

            **30** programmer profiles

            **{stats['submissions']}** programming submissions

            Used to learn programming behavior.
            """
        )

    with col2:

        st.success(
            """
            **K-Means Model**

            **5** behavioral clusters

            **11** ML features

            Used to classify programming styles.
            """
        )

    with col3:

        st.warning(
            """
            **Behavior Analysis**

            Tracks:

            Complexity • Optimization •
            Algorithms • Data Structures
            """
        )

    # -----------------------------------------------------
    # WHAT CAN YOU DO?
    # -----------------------------------------------------

    st.subheader(
        "🚀 Explore the Analyzer"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            """
            ### 🔍 Analyze Code

            Paste a Python solution and get:

            - Complexity analysis
            - AST analysis
            - Algorithm patterns
            - Data structures
            - ML behavioral profile
            """
        )

    with col2:

        st.markdown(
            """
            ### 🧠 Programmer Profiles

            Explore historical programming behavior:

            - AI-generated profiles
            - Cluster membership
            - Strengths & weaknesses
            - Programming trends
            - AI recommendations
            """
        )

    st.divider()

    # -----------------------------------------------------
    # WHAT THE AI ANALYZES
    # -----------------------------------------------------

    st.subheader(
        "🧠 What the AI Analyzes"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(
            """
            ### 📊 Code Quality

            - Cyclomatic complexity
            - Maintainability
            - Code structure
            - Complexity trends
            """
        )

    with col2:

        st.markdown(
            """
            ### 🔎 Programming Behavior

            - Algorithm diversity
            - Data-structure usage
            - Recursion
            - Brute-force tendency
            """
        )

    with col3:

        st.markdown(
            """
            ### 🚀 Problem Solving

            - Optimization
            - Problem-solving diversity
            - Improvement trends
            - Algorithmic patterns
            """
        )

    # -----------------------------------------------------
    # MODEL PIPELINE
    # -----------------------------------------------------

    st.subheader(
        "⚙️ How the AI Works"
    )

    st.markdown(
        """
        ```text
        Python Code
             ↓
        AST + Complexity Analysis
             ↓
        Behavioral Features
             ↓
        11-Dimensional ML Vector
             ↓
        StandardScaler
             ↓
        K-Means Clustering
             ↓
        Programmer Behavioral Profile
        ```
        """
    )

    st.caption(
        "The system learns programming behavior from "
        "historical submissions rather than evaluating "
        "a programmer from a single solution."
    )
# =========================================================
# ANALYZE CODE
# =========================================================

elif page == "Analyze Code":

    st.header("🔍 Analyze Code")

    st.write(
        "Paste Python code below and let the AI analyze "
        "your programming style."
    )

    # -------------------------------------------------
    # SELECT PROGRAMMER
    # -------------------------------------------------

    database = Database(str(DB_PATH))

    cursor = database.connection.cursor()

    cursor.execute("""
        SELECT id, username
        FROM users
        ORDER BY username
    """)

    programmers = cursor.fetchall()

    if not programmers:

        st.warning(
            "No programmers found in the database."
        )

        database.close()
        st.stop()

    programmer_names = [
        programmer["username"]
        for programmer in programmers
    ]

    selected_username = st.selectbox(
        "Programmer",
        programmer_names
    )

    selected_programmer = next(
        programmer
        for programmer in programmers
        if programmer["username"] == selected_username
    )

    problem_name = st.text_input(
        "Problem Name",
        value="Analyzed Code"
    )

    code = st.text_area(
        "Python Code",
        height=400,
        placeholder=(
            "def two_sum(nums, target):\n\n"
            "    seen = {}\n\n"
            "    for i, value in enumerate(nums):\n\n"
            "        needed = target - value\n\n"
            "        if needed in seen:\n"
            "            return [seen[needed], i]\n\n"
            "        seen[value] = i\n\n"
            "    return []"
        )
    )

    if st.button(
        "🚀 Analyze Code",
        type="primary"
    ):

        if not code.strip():

            st.warning(
                "Please enter some Python code."
            )

        else:

            with st.spinner(
                "Analyzing your code..."
            ): 

                analysis = (
                    inference_engine.analyze_code(
                        code
                    )
                )

            # -------------------------------------------------
            # VALIDATION
            # -------------------------------------------------

            if not analysis["valid"]:

                st.error(
                    "❌ Code analysis failed."
                )

                st.code(
                    analysis["error"]
                )

            else:

                # =============================================
                # SAVE SUBMISSION
                # =============================================

                submission_id = database.save_submission(
                    user_id=selected_programmer["id"],
                    problem_name=problem_name,
                    language="Python",
                    code=code
                )

                st.write(
                    "DEBUG submission ID:",
                    submission_id
                )

                database.save_features(
                    submission_id=submission_id,
                    features=analysis["ast"],
                    complexity=analysis["complexity"]
                )

                st.success(
                    f"Submission saved for **{selected_username}**."
                )

                # =============================================
                # ML PREDICTION
                # =============================================

                prediction = (
                    inference_engine.predict(
                        analysis
                    )
                )

                predicted_cluster = (
                    prediction["cluster"]
                )

                membership = (
                    prediction["memberships"]
                )

                primary_membership = (
                    membership[
                        predicted_cluster
                    ] * 100
                )

                profile = PROFILE_NAMES[
                    predicted_cluster
                ]

                # =============================================
                # AI PROFILE
                # =============================================

                st.divider()

                st.subheader(
                    "🧠 AI Programmer Profile"
                )

                profile_col1, profile_col2 = (
                    st.columns([2, 1])
                )

                with profile_col1:

                    st.success(
                        f"### {profile}"
                    )

                    st.write(
                        "The submitted code most closely "
                        "matches this learned programming "
                        "behavior cluster."
                    )

                with profile_col2:

                    st.metric(
                        "Primary Membership",
                        f"{primary_membership:.2f}%"
                    )

                # =============================================
                # CODE METRICS
                # =============================================

                st.subheader(
                    "📊 Code Metrics"
                )

                complexity = analysis[
                    "complexity"
                ]

                avg_complexity = (
                    complexity[
                        "cyclomatic_complexity"
                    ]["average"]
                )

                max_complexity = (
                    complexity[
                        "cyclomatic_complexity"
                    ]["maximum"]
                )

                maintainability = (
                    complexity[
                        "maintainability_index"
                    ]
                )

                features = analysis[
                    "features"
                ]

                col1, col2, col3, col4 = (
                    st.columns(4)
                )

                with col1:

                    st.metric(
                        "Complexity",
                        f"{avg_complexity:.2f}"
                    )

                with col2:

                    st.metric(
                        "Max Complexity",
                        max_complexity
                    )

                with col3:

                    st.metric(
                        "Maintainability",
                        f"{maintainability:.2f}"
                    )

                with col4:

                    st.metric(
                        "Optimization",
                        f"{features['optimization_score']:.1f}"
                    )

                # =============================================
                # BEHAVIOR METRICS
                # =============================================

                st.subheader(
                    "🔬 Programming Behavior"
                )

                col1, col2, col3, col4 = (
                    st.columns(4)
                )

                with col1:

                    st.metric(
                        "Algorithm Diversity",
                        f"{features['algorithm_diversity']:.1f}"
                    )

                with col2:

                    st.metric(
                        "Data Structure Diversity",
                        f"{features['data_structure_diversity']:.1f}"
                    )

                with col3:

                    st.metric(
                        "Brute Force",
                        f"{features['brute_force_tendency']:.1f}"
                    )

                with col4:

                    st.metric(
                        "Problem Solving",
                        f"{features['problem_solving_diversity']:.1f}"
                    )

                # =============================================
                # CLUSTER MEMBERSHIP
                # =============================================

                st.subheader(
                    "🎯 AI Cluster Membership"
                )

                membership_data = {
                    PROFILE_NAMES[i]:
                    float(membership[i] * 100)
                    for i in range(5)
                }

                st.bar_chart(
                    membership_data,
                    horizontal=True
                )

                # =============================================
                # AST ANALYSIS
                # =============================================

                st.subheader(
                    "🌳 AST Analysis"
                )

                ast_result = analysis[
                    "ast"
                ]

                col1, col2, col3, col4 = (
                    st.columns(4)
                )

                with col1:

                    st.metric(
                        "Functions",
                        ast_result.get(
                            "num_functions",
                            0
                        )
                    )

                with col2:

                    st.metric(
                        "Loops",
                        ast_result.get(
                            "total_loops",
                            0
                        )
                    )

                with col3:

                    st.metric(
                        "Nested Loops",
                        ast_result.get(
                            "nested_loops",
                            0
                        )
                    )

                with col4:

                    st.metric(
                        "Recursion",
                        ast_result.get(
                            "recursive_functions",
                            0
                        )
                    )

                # =============================================
                # DATA STRUCTURES
                # =============================================

                st.subheader(
                    "📦 Data Structures"
                )

                data_structures = ast_result.get(
                    "data_structures",
                    {}
                )

                st.json(
                    data_structures
                )

                # =============================================
                # PATTERNS
                # =============================================

                st.subheader(
                    "🔎 Detected Patterns"
                )

                patterns = ast_result.get(
                    "patterns",
                    []
                )

                if patterns:

                    st.json(
                        patterns
                    )

                else:

                    st.info(
                        "No recognized algorithmic "
                        "patterns detected."
                    )

                # =============================================
                # ORIGINAL CODE
                # =============================================

                with st.expander(
                    "View analyzed code"
                ): 

                    st.code(
                        code,
                        language="python"
                    )


# =========================================================
# PROGRAMMER PROFILE
# =========================================================

elif page == "Programmer Profile":

    st.header("🧠 Programmer Profile")

    # -----------------------------------------------------
    # GET PROGRAMMERS
    # -----------------------------------------------------

    cursor = db.cursor()

    cursor.execute("""
        SELECT id, username
        FROM users
        ORDER BY username
    """)

    users = cursor.fetchall()

    if not users:

        st.warning(
            "No programmers found in the database."
        )

    else:

        # -------------------------------------------------
        # PROGRAMMER SELECTOR
        # -------------------------------------------------

        user_names = [
            user["username"]
            for user in users
        ]

        selected_username = st.selectbox(
            "Select Programmer",
            user_names
        )

        selected_user = next(
            user
            for user in users
            if user["username"] == selected_username
        )

        # -------------------------------------------------
        # GET SUBMISSION HISTORY
        # -------------------------------------------------

        database = Database(str(DB_PATH))

        history = list(
            reversed(
                database.get_user_submissions(
                    selected_user["id"]
                )
            )
        )

        database.close()

        behavior_analyzer = BehaviorAnalyzer()

        behavior = behavior_analyzer.analyze(
            history
        )

        if not behavior["valid"]:

            st.error(
                behavior["error"]
            )

        else:

            # =============================================
            # ML FEATURES
            # =============================================

            feature_builder = MLFeatureBuilder()

            ml_features = feature_builder.build(
                behavior
            )

            # =============================================
            # ML PROFILE
            # =============================================

            predicted_cluster, membership = (
                get_programmer_ml_profile(
                    ml_features
                )
            )

            profile_name = PROFILE_NAMES[
                predicted_cluster
            ]

            primary_membership = (
                membership[predicted_cluster] * 100
            )

            style = behavior[
                "programming_style"
            ]

            scores = behavior["scores"]
            metrics = behavior["metrics"]
            trends = behavior["trends"]

            # =============================================
            # HERO PROFILE
            # =============================================

            st.divider()

            hero_col1, hero_col2 = st.columns(
                [3, 1]
            )

            with hero_col1:

                st.subheader(
                    "🤖 AI Programmer Profile"
                )

                st.success(
                    f"### {profile_name}"
                )

                st.write(
                    f"Behavioral profile for **{selected_username}**, "
                    f"based on {behavior['submissions_analyzed']} submissions."
                )

            with hero_col2:

                st.metric(
                    "Primary Membership",
                    f"{primary_membership:.2f}%"
                )

            # =============================================
            # AI ASSESSMENT
            # =============================================

            st.subheader("🤖 AI Assessment")

            summary_parts = []

            if scores["algorithm_diversity"] >= 70:
                summary_parts.append(
                    "Your solutions show strong algorithmic diversity."
                )
            elif scores["algorithm_diversity"] >= 40:
                summary_parts.append(
                    "You use a reasonably diverse range of algorithms."
                )
            else:
                summary_parts.append(
                    "Your solutions currently rely on a relatively small "
                    "range of algorithmic techniques."
                )

            if scores["optimization"] >= 70:
                summary_parts.append(
                    "You show a strong tendency toward optimized approaches."
                )
            elif scores["optimization"] >= 40:
                summary_parts.append(
                    "You demonstrate a moderate focus on optimization."
                )
            else:
                summary_parts.append(
                    "There is room to explore more optimized approaches."
                )

            if scores["code_quality"] >= 80:
                summary_parts.append(
                    "Your code quality and maintainability are strong."
                )
            elif scores["code_quality"] >= 60:
                summary_parts.append(
                    "Your code generally maintains a reasonable level of quality."
                )
            else:
                summary_parts.append(
                    "Improving code maintainability would strengthen your solutions."
                )

            if scores["improvement"] >= 60:
                summary_parts.append(
                    "Your recent solutions show a strong improvement trend."
                )
            elif scores["improvement"] >= 30:
                summary_parts.append(
                    "Your solutions show signs of gradual improvement."
                )

            if trends.get("available"):

                complexity_change = (
                    trends["recent_complexity"]
                    - trends["early_complexity"]
                )

                if complexity_change > 0.5:
                    summary_parts.append(
                        "However, your recent solutions have become more complex, "
                        "so simplifying some approaches could improve maintainability."
                    )
                elif complexity_change < -0.5:
                    summary_parts.append(
                        "Your recent solutions have become less complex, "
                        "suggesting a more efficient problem-solving approach."
                    )

            st.info(" ".join(summary_parts))

            # =============================================
            # QUICK DIAGNOSIS
            # =============================================

            st.subheader("🎯 Quick Diagnosis")

            diagnosis_col1, diagnosis_col2 = st.columns(2)

            with diagnosis_col1:

                st.markdown("### 💪 What you're doing well")

                if behavior["strengths"]:

                    for strength in behavior["strengths"]:
                        st.success(f"✓ {strength}")

                else:
                    st.write("No major strengths detected yet.")

            with diagnosis_col2:

                st.markdown("### 🚀 What to work on")

                if behavior["weaknesses"]:

                    for weakness in behavior["weaknesses"]:
                        st.warning(f"→ {weakness}")

                else:
                    st.write("No major weaknesses detected.")

            # =============================================
            # KEY METRICS
            # =============================================

            st.divider()

            st.subheader("📊 Key Metrics")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Avg Complexity",
                    f"{ml_features['average_complexity']:.2f}"
                )

            with col2:
                st.metric(
                    "Maintainability",
                    f"{ml_features['average_maintainability']:.2f}"
                )

            with col3:
                st.metric(
                    "Optimization",
                    f"{ml_features['optimization_score']:.1f}"
                )

            with col4:
                st.metric(
                    "Improvement",
                    f"{ml_features['improvement_score']:.1f}"
                )

            # =============================================
            # PROGRAMMING BEHAVIOR
            # =============================================

            st.subheader("🧠 Programming Behavior")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Algorithm Diversity",
                    f"{ml_features['algorithm_diversity']:.1f}"
                )

            with col2:
                st.metric(
                    "Data Structure Diversity",
                    f"{ml_features['data_structure_diversity']:.1f}"
                )

            with col3:
                st.metric(
                    "Brute Force",
                    f"{ml_features['brute_force_tendency']:.1f}"
                )

            with col4:
                st.metric(
                    "Problem Solving",
                    f"{ml_features['problem_solving_diversity']:.1f}"
                )

            # =============================================
            # PROGRAMMING STYLE
            # =============================================

            st.subheader("🎨 Programming Style")

            style_col1, style_col2 = st.columns([2, 1])

            with style_col1:

                st.success(
                    f"### {style['name']}"
                )

                st.write(style["reason"])

            with style_col2:

                st.metric(
                    "Submissions Analyzed",
                    behavior["submissions_analyzed"]
                )

            # =============================================
            # CLUSTER MEMBERSHIP
            # =============================================

            st.subheader("🎯 Behavioral Cluster Membership")

            membership_data = {
                PROFILE_NAMES[i]:
                float(membership[i] * 100)
                for i in range(len(membership))
            }

            st.bar_chart(
                membership_data,
                horizontal=True
            )

            # =============================================
            # CODING HABITS
            # =============================================

            st.subheader("💻 Coding Habits")

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Nested Loop Usage",
                    f"{ml_features['nested_loop_percentage']:.1f}%"
                )

            with col2:
                st.metric(
                    "Recursion Usage",
                    f"{ml_features['recursion_percentage']:.1f}%"
                )

            # =============================================
            # ALGORITHMS + DATA STRUCTURES
            # =============================================

            st.subheader("🔎 Algorithms & Data Structures")

            patterns = metrics["algorithm_patterns"]
            structures = metrics["data_structures"]

            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:

                st.markdown("### 🔎 Algorithm Patterns")

                pattern_data = {
                    name: count
                    for name, count in patterns.items()
                    if count > 0
                }

                if pattern_data:
                    st.bar_chart(
                        pattern_data,
                        horizontal=True
                    )
                else:
                    st.info("No algorithm patterns detected.")

            with chart_col2:

                st.markdown("### 📦 Data Structures")

                structure_data = {
                    name: count
                    for name, count in structures.items()
                    if count > 0
                }

                if structure_data:
                    st.bar_chart(
                        structure_data,
                        horizontal=True
                    )
                else:
                    st.info("No data structures detected.")

            # =============================================
            # PROGRAMMING TRENDS
            # =============================================

            st.subheader("📈 Programming Trends")

            complexity_values = []
            maintainability_values = []

            for submission in history:

                complexity = submission["cyclomatic_complexity"]
                maintainability = submission["maintainability_index"]

                if complexity is not None:
                    complexity_values.append(float(complexity))

                if maintainability is not None:
                    maintainability_values.append(float(maintainability))

            if complexity_values:

                st.markdown("**Cyclomatic Complexity Over Time**")

                st.line_chart(
                    complexity_values,
                    x_label="Submission",
                    y_label="Complexity"
                )

            else:
                st.info("Not enough complexity data available.")

            if maintainability_values:

                st.markdown("**Maintainability Over Time**")

                st.line_chart(
                    maintainability_values,
                    x_label="Submission",
                    y_label="Maintainability"
                )

            else:
                st.info("Not enough maintainability data available.")

            # =============================================
            # TREND SUMMARY
            # =============================================

            if trends.get("available"):

                st.markdown("### Trend Summary")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Early Complexity",
                        f"{trends['early_complexity']:.2f}"
                    )

                with col2:
                    st.metric(
                        "Recent Complexity",
                        f"{trends['recent_complexity']:.2f}",
                        delta=(
                            f"{trends['complexity_improvement']:.2f}%"
                        )
                    )

                with col3:
                    st.metric(
                        "Maintainability Change",
                        f"{trends['maintainability_change']:.2f}"
                    )

            else:
                st.info(trends["message"])

            # =============================================
            # AI RECOMMENDATIONS
            # =============================================

            st.subheader("💡 AI Recommendations")

            recommendations = behavior["recommendations"]

            if recommendations:

                for recommendation in recommendations:
                    st.info(f"→ {recommendation}")

            else:
                st.write("No additional recommendations.")


elif page == "History":

    st.header("📚 Programming History")

    cursor = db.cursor()

    cursor.execute("""
        SELECT
            submissions.problem_name,
            submissions.language,
            submissions.submitted_at,
            code_features.cyclomatic_complexity,
            code_features.maintainability_index
        FROM submissions

        LEFT JOIN code_features
            ON submissions.id =
               code_features.submission_id

        ORDER BY submissions.id DESC
        LIMIT 20
    """)

    history = cursor.fetchall()

    if not history:

        st.info(
            "No submissions found."
        )

    else:

        for submission in history:

            problem = (
                submission["problem_name"]
                or "Unnamed Problem"
            )

            complexity = (
                submission[
                    "cyclomatic_complexity"
                ]
            )

            maintainability = (
                submission[
                    "maintainability_index"
                ]
            )

            with st.container(
                border=True
            ):

                col1, col2, col3, col4 = (
                    st.columns(4)
                )

                with col1:

                    st.write(
                        f"**{problem}**"
                    )

                with col2:

                    st.write(
                        submission["language"]
                    )

                with col3:

                    st.write(
                        f"Complexity: "
                        f"{complexity:.2f}"
                        if complexity is not None
                        else "Complexity: —"
                    )

                with col4:

                    st.write(
                        f"Maintainability: "
                        f"{maintainability:.2f}"
                        if maintainability is not None
                        else "Maintainability: —"
                    )