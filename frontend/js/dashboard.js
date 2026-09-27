const API_URL = "http://127.0.0.1:8000";


const token =
    localStorage.getItem("access_token");


if (!token) {

    window.location.href =
        "login.html";

}


async function loadDashboard() {

    try {

        const response =
            await fetch(
                `${API_URL}/profile/me`,
                {
                    headers: {
                        "Authorization":
                            `Bearer ${token}`
                    }
                }
            );


        if (response.status === 401) {

            localStorage.clear();

            window.location.href =
                "login.html";

            return;
        }


        const data =
            await response.json();


        document.getElementById(
            "dashboardMessage"
        ).textContent = "";


        document.getElementById(
            "dashboardMessage"
        ).className = "message";


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to load dashboard."
            );

        }


        // -------------------------------------------------
        // USER
        // -------------------------------------------------

        document.getElementById(
            "username"
        ).textContent =
            data.username;


        // -------------------------------------------------
        // STATS
        // -------------------------------------------------

        document.getElementById(
            "submissions"
        ).textContent =
            data.submissions;


        document.getElementById(
            "complexity"
        ).textContent =
            data.average_complexity.toFixed(2);


        document.getElementById(
            "quality"
        ).textContent =
            data.code_quality_score.toFixed(1);


        document.getElementById(
            "optimization"
        ).textContent =
            data.optimization_score.toFixed(1);


        // -------------------------------------------------
        // PROFILE SCORES
        // -------------------------------------------------

        setScore(
            "qualityBar",
            "qualityScore",
            data.code_quality_score
        );


        setScore(
            "optimizationBar",
            "optimizationScore",
            data.optimization_score
        );


        setScore(
            "algorithmBar",
            "algorithmScore",
            data.algorithm_diversity
        );


        setScore(
            "problemBar",
            "problemScore",
            data.problem_solving_diversity
        );

        // -------------------------------------------------
        // AI INSIGHTS
        // -------------------------------------------------
        const insights = data.ai_insights;

        if (insights) {
            document.getElementById(
                "insightStrength"
            ).textContent =
                insights.strength || "—";

            document.getElementById(
                "insightWeakness"
            ).textContent =
                insights.weakness || "—";

            document.getElementById(
                "insightComplexity"
            ).textContent =
                insights.complexity || "—";

            document.getElementById(
                "insightRecommendation"
            ).textContent =
                insights.recommendation || "—";

            document.getElementById(
                "insightProgress"
            ).textContent =
                insights.progress || "—";
        }

        renderPerformanceChart(
            data.trend || []
        );

        displayBehavioralProfile(
            data.behavioral_profile
        );

    }

    catch (error) {

        const message =
            document.getElementById(
                "dashboardMessage"
            );

        message.textContent =
            error.message;

        message.className =
            "message error";

    }

}


function setScore(
    barId,
    textId,
    value
) {

    const bar =
        document.getElementById(barId);

    const text =
        document.getElementById(textId);


    if (!bar || !text) {

        console.error(
            "Score element missing:",
            {
                barId,
                textId
            }
        );

        return;
    }


    const safeValue =
        Math.max(
            0,
            Math.min(
                100,
                Number(value) || 0
            )
        );


    bar.style.width =
        `${safeValue}%`;


    text.textContent =
        safeValue.toFixed(1);

}


// =========================================================
// BEHAVIORAL PROFILE
// =========================================================

function displayBehavioralProfile(profile) {

    if (!profile) {
        return;
    }


    const requiredElements = [
        "strongestHabit",
        "strongestHabitScore",
        "weakestHabit",
        "weakestHabitScore",
        "hashMapBar",
        "hashMapScore",
        "setBar",
        "setScore",
        "recursionBar",
        "recursionScore",
        "nestedLoopBar",
        "nestedLoopScore",
        "bruteForceBar",
        "bruteForceScore",
        "recurringPatterns",
        "behaviorSummary"
    ];


    for (const id of requiredElements) {


        if (!document.getElementById(id)) {


            console.error(
                `Missing dashboard element: ${id}`
            );


            return;
        }
    }


    // -----------------------------------------------------
    // BEHAVIOR SCORES
    // -----------------------------------------------------

    if (profile.behavior_scores) {

        setBehavior(
            "hashMapBar",
            "hashMapScore",
            profile.behavior_scores.hash_map_preference
        );

        setBehavior(
            "setBar",
            "setScore",
            profile.behavior_scores.set_preference
        );

        setBehavior(
            "recursionBar",
            "recursionScore",
            profile.behavior_scores.recursion_tendency
        );

        setBehavior(
            "nestedLoopBar",
            "nestedLoopScore",
            profile.behavior_scores.nested_loop_tendency
        );

        setBehavior(
            "bruteForceBar",
            "bruteForceScore",
            profile.behavior_scores.brute_force_tendency
        );

    }

    // -----------------------------------------------------
    // HABITS
    // -----------------------------------------------------

    if (profile.strongest_habit) {

        document.getElementById(
            "strongestHabit"
        ).textContent =
            `${profile.strongest_habit.name} (${profile.strongest_habit.score.toFixed(1)}%)`;

    }

    if (profile.weakest_habit) {

        document.getElementById(
            "weakestHabit"
        ).textContent =
            `${profile.weakest_habit.name} (${profile.weakest_habit.score.toFixed(1)}%)`;

    }

    // -----------------------------------------------------
    // PATTERNS
    // -----------------------------------------------------

    if (profile.patterns) {

        const container =
            document.getElementById(
                "recurringPatterns"
            );

        container.innerHTML = "";

        profile.patterns.forEach(
            function (item) {

                const tag =
                    document.createElement(
                        "div"
                    );

                tag.className =
                    "pattern-tag";

                const name =
                    document.createElement(
                        "span"
                    );

                name.className =
                    "pattern-name";

                name.textContent =
                    formatPatternName(
                        item.pattern
                    );

                const frequency =
                    document.createElement(
                        "span"
                    );

                frequency.textContent =
                    `${item.percentage}% of submissions`;

                tag.appendChild(name);

                tag.appendChild(frequency);

                container.appendChild(tag);

            }
        );

    }

    // -----------------------------------------------------
    // SUMMARY
    // -----------------------------------------------------

    document.getElementById(
        "behaviorSummary"
    ).textContent =
        profile.summary ||
        "Continue analyzing submissions to discover more patterns.";

}


function setBehavior(
    barId,
    textId,
    value
) {

    const bar =
        document.getElementById(barId);

    const text =
        document.getElementById(textId);


    if (!bar || !text) {

        console.error(
            "Behavior element missing:",
            {
                barId,
                textId
            }
        );

        return;
    }


    const safeValue =
        Math.max(
            0,
            Math.min(
                100,
                Number(value) || 0
            )
        );


    bar.style.width =
        `${safeValue}%`;


    text.textContent =
        `${safeValue.toFixed(1)}%`;

}


function formatPatternName(value) {

    return String(value || "")
        .replaceAll("_", " ")
        .replace(
            /\b\w/g,
            character =>
                character.toUpperCase()
        );

}

// =========================================================
// PERFORMANCE CHART
// =========================================================

let performanceChart = null;


function renderPerformanceChart(trend) {

    const canvas =
        document.getElementById(
            "performanceChart"
        );

    if (!canvas || !Array.isArray(trend)) {
        return;
    }


    // Destroy previous chart if one exists
    if (performanceChart) {
        performanceChart.destroy();
    }


    const labels =
        trend.map(
            (item, index) =>
                `#${index + 1}`
        );


    const quality =
        trend.map(
            item =>
                Number(item.quality) || 0
        );


    const optimization =
        trend.map(
            item =>
                Number(item.optimization) || 0
        );


    const complexity =
        trend.map(
            item =>
                Number(item.complexity) || 0
        );


    performanceChart =
        new Chart(
            canvas,
            {
                type: "line",

                data: {

                    labels,

                    datasets: [

                        {
                            label: "Code Quality",

                            data: quality,

                            borderColor: "#22c55e",

                            backgroundColor: "rgba(34, 197, 94, 0.12)",

                            tension: 0.35,

                            borderWidth: 3,

                            pointRadius: 4,

                            pointHoverRadius: 6,

                            fill: true
                        },

                        {
                            label: "Optimization",

                            data: optimization,

                            borderColor: "#3b82f6",

                            backgroundColor: "rgba(59, 130, 246, 0.12)",

                            tension: 0.35,

                            borderWidth: 3,

                            pointRadius: 4,

                            pointHoverRadius: 6,

                            fill: true
                        },

                        {
                            label: "Complexity",

                            data: complexity,

                            borderColor: "#f59e0b",

                            backgroundColor: "rgba(245, 158, 11, 0.08)",

                            tension: 0.35,

                            borderWidth: 3,

                            pointRadius: 4,

                            pointHoverRadius: 6,

                            fill: false
                        }

                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    interaction: {
                        intersect: false,
                        mode: "index"
                    },

                    plugins: {

                        legend: {
                            display: false
                        },

                        tooltip: {
                            enabled: true
                        }

                    },

                    scales: {

                        x: {

                            grid: {
                                display: false
                            },

                            ticks: {
                                color: "#777783"
                            }

                        },

                        y: {

                            beginAtZero: true,

                            suggestedMax: 100,

                            grid: {
                                color: "#24242e"
                            },

                            ticks: {
                                color: "#777783"
                            }

                        }

                    }

                }

            }
        );

}

// =========================================================
// LOGOUT
// =========================================================

document
    .getElementById("logoutButton")
    .addEventListener(
        "click",
        function () {

            localStorage.clear();

            window.location.href =
                "login.html";

        }
    );


loadDashboard();