const API_URL = "https://aianalyser-4iaf.onrender.com";

const token =
    localStorage.getItem("access_token");


if (!token) {
    window.location.href = "login.html";
}


// =========================================================
// LOAD PROFILE
// =========================================================

async function loadProfile() {

    const message =
        document.getElementById("profileMessage");

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


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to load profile."
            );

        }


        message.textContent = "";
        message.className = "message";


        displayOverview(data);

        displayDNA(data);

        displayBehavior(
            data.behavioral_profile
        );

        displayGrowth(
            data.trend || []
        );

        displayInsights(
            data.ai_insights
        );

        displayCluster(data);


    }

    catch (error) {

        message.textContent =
            error.message;

        message.className =
            "message error";

    }

}


// =========================================================
// OVERVIEW
// =========================================================

function displayOverview(data) {

    document.getElementById(
        "username"
    ).textContent =
        data.username || "Programmer";


    document.getElementById(
        "submissions"
    ).textContent =
        data.submissions ?? 0;


    document.getElementById(
        "complexity"
    ).textContent =
        Number(
            data.average_complexity || 0
        ).toFixed(2);


    document.getElementById(
        "quality"
    ).textContent =
        Number(
            data.code_quality_score || 0
        ).toFixed(1);


    document.getElementById(
        "optimization"
    ).textContent =
        Number(
            data.optimization_score || 0
        ).toFixed(1);


    document.getElementById(
        "programmerType"
    ).textContent =
        getProgrammerType(data);


    document.getElementById(
        "profileSummary"
    ).textContent =
        getProfileSummary(data);

}


// =========================================================
// PROGRAMMER TYPE
// =========================================================

function getProgrammerType(data) {

    const optimization =
        Number(data.optimization_score || 0);

    const quality =
        Number(data.code_quality_score || 0);

    const algorithm =
        Number(data.algorithm_diversity || 0);

    const problem =
        Number(data.problem_solving_diversity || 0);

    const behavior =
        data.behavioral_profile?.behavior_scores || {};


    const hashMap =
        Number(
            behavior.hash_map_preference || 0
        );

    const recursion =
        Number(
            behavior.recursion_tendency || 0
        );

    const nestedLoops =
        Number(
            behavior.nested_loop_tendency || 0
        );

    const bruteForce =
        Number(
            behavior.brute_force_tendency || 0
        );


    // -----------------------------------------
    // EFFICIENCY-ORIENTED
    // -----------------------------------------

    if (
        optimization >= 75 &&
        quality >= 65 &&
        nestedLoops < 45 &&
        bruteForce < 45
    ) {
        return "Efficiency-Oriented Programmer";
    }


    // -----------------------------------------
    // HASHING SPECIALIST
    // -----------------------------------------

    if (
        hashMap >= 60 &&
        optimization >= 65
    ) {
        return "Hashing-Oriented Problem Solver";
    }


    // -----------------------------------------
    // ALGORITHM EXPLORER
    // -----------------------------------------

    if (
        algorithm >= 55 &&
        problem >= 55
    ) {
        return "Algorithm Explorer";
    }


    // -----------------------------------------
    // RECURSIVE THINKER
    // -----------------------------------------

    if (
        recursion >= 55
    ) {
        return "Recursive Problem Solver";
    }


    // -----------------------------------------
    // STRATEGIC PROBLEM SOLVER
    // -----------------------------------------

    if (
        problem >= 60 &&
        quality >= 60
    ) {
        return "Strategic Problem Solver";
    }


    // -----------------------------------------
    // CLEAN CODE PROGRAMMER
    // -----------------------------------------

    if (
        quality >= 75 &&
        optimization >= 60
    ) {
        return "Clean Code Programmer";
    }


    // -----------------------------------------
    // EXPERIMENTAL
    // -----------------------------------------

    if (
        bruteForce >= 60 ||
        nestedLoops >= 60
    ) {
        return "Experimental Problem Solver";
    }


    return "Developing Programmer";
}


// =========================================================
// PROFILE SUMMARY
// =========================================================

function getProfileSummary(data) {

    const type =
        getProgrammerType(data);

    const submissions =
        Number(data.submissions || 0);

    const behavior =
        data.behavioral_profile || {};

    const strongest =
        behavior.strongest_habit?.name;


    if (submissions < 3) {

        return (
            "Your profile is still developing. " +
            "Analyze more solutions to reveal stronger " +
            "programming patterns."
        );

    }


    if (strongest) {

        return (
            `You currently show the traits of a ` +
            `${type.toLowerCase()}. ` +
            `Your strongest recurring habit is ` +
            `${strongest.toLowerCase()}.`
        );

    }


    return (
        `Your current profile suggests a ` +
        `${type.toLowerCase()}. ` +
        `Continue analyzing different types of problems ` +
        `to make this profile more accurate.`
    );

}


// =========================================================
// PROGRAMMING DNA
// =========================================================

function displayDNA(data) {

    setDNA(
        "qualityBar",
        "qualityScore",
        data.code_quality_score
    );


    setDNA(
        "optimizationBar",
        "optimizationScore",
        data.optimization_score
    );


    setDNA(
        "algorithmBar",
        "algorithmScore",
        data.algorithm_diversity
    );


    setDNA(
        "dataStructureBar",
        "dataStructureScore",
        data.data_structure_diversity
    );


    setDNA(
        "problemBar",
        "problemScore",
        data.problem_solving_diversity
    );

}


function setDNA(
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
            "Missing DNA element:",
            barId,
            textId
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
        `${safeValue.toFixed(1)}`;

}


// =========================================================
// BEHAVIOR
// =========================================================

function displayBehavior(profile) {

    if (!profile) {
        return;
    }


    const scores =
        profile.behavior_scores || {};


    setBehavior(
        "hashMapBar",
        "hashMapScore",
        scores.hash_map_preference
    );


    setBehavior(
        "setBar",
        "setScore",
        scores.set_preference
    );


    setBehavior(
        "recursionBar",
        "recursionScore",
        scores.recursion_tendency
    );


    setBehavior(
        "nestedLoopBar",
        "nestedLoopScore",
        scores.nested_loop_tendency
    );


    setBehavior(
        "bruteForceBar",
        "bruteForceScore",
        scores.brute_force_tendency
    );


    if (profile.strongest_habit) {

        document.getElementById(
            "strongestHabit"
        ).textContent =
            profile.strongest_habit.name;


        document.getElementById(
            "strongestHabitScore"
        ).textContent =
            `${Number(
                profile.strongest_habit.score || 0
            ).toFixed(1)}%`;

    }


    if (profile.weakest_habit) {

        document.getElementById(
            "weakestHabit"
        ).textContent =
            profile.weakest_habit.name;


        document.getElementById(
            "weakestHabitScore"
        ).textContent =
            `${Number(
                profile.weakest_habit.score || 0
            ).toFixed(1)}%`;

    }


    displayPatterns(
        profile.patterns || [],
        profile.pattern_insights || []
    );

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


// =========================================================
// RECURRING PATTERNS
// =========================================================

function displayPatterns(
    patterns,
    insights
) {

    const container =
        document.getElementById(
            "recurringPatterns"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    // =====================================================
    // NO PATTERNS
    // =====================================================

    if (!patterns.length) {

        container.innerHTML = `
            <span class="profile-no-patterns">
                No strong recurring techniques detected yet.
            </span>
        `;

        return;
    }


    // =====================================================
    // HEADER
    // =====================================================

    const heading =
        document.createElement("div");

    heading.className =
        "profile-pattern-heading";

    heading.textContent =
        "Recurring Techniques";


    container.appendChild(
        heading
    );


    // =====================================================
    // INSIGHT CARDS
    // =====================================================

    const data =
        insights.length
            ? insights
            : patterns;


    data.forEach(
        function (item) {

            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "profile-pattern";


            const name =
                document.createElement(
                    "strong"
                );

            name.textContent =
                formatPattern(
                    item.name ||
                    item.pattern
                );


            const frequency =
                document.createElement(
                    "span"
                );

            const percentage =
                Number(
                    item.percentage || 0
                );


            const occurrences =
                Number(
                    item.occurrences || 0
                );


            frequency.textContent =
                `${occurrences} of your submissions · ` +
                `${percentage.toFixed(0)}%`;


            card.appendChild(
                name
            );

            card.appendChild(
                frequency
            );


            // -------------------------------------------------
            // Insight message
            // -------------------------------------------------

            if (item.message) {

                const message =
                    document.createElement(
                        "p"
                    );

                message.className =
                    "profile-pattern-message";

                message.textContent =
                    item.message;

                card.appendChild(
                    message
                );

            }


            container.appendChild(
                card
            );

        }
    );

}


function formatPattern(value) {

    return String(value || "")
        .replaceAll("_", " ")
        .replace(
            /\b\w/g,
            character =>
                character.toUpperCase()
        );

}


// =========================================================
// GROWTH
// =========================================================

function displayGrowth(trend) {

    const container =
        document.getElementById(
            "growthChart"
        );


    const status =
        document.getElementById(
            "growthStatus"
        );


    if (!container || !status) {
        return;
    }


    container.innerHTML = "";


    if (!trend.length) {

        container.innerHTML = `
            <div class="growth-empty">
                Analyze more submissions to see your growth.
            </div>
        `;

        status.textContent =
            "Not enough data";

        return;
    }


    const maxValue =
        Math.max(
            ...trend.map(
                item =>
                    Math.max(
                        Number(item.quality) || 0,
                        Number(item.optimization) || 0
                    )
            ),
            100
        );


    trend.forEach(
        function (item, index) {

            const quality =
                Number(
                    item.quality || 0
                );


            const optimization =
                Number(
                    item.optimization || 0
                );


            const point =
                document.createElement(
                    "div"
                );

            point.className =
                "growth-point";


            const label =
                document.createElement(
                    "span"
                );

            label.textContent =
                `#${index + 1}`;


            const bars =
                document.createElement(
                    "div"
                );

            bars.className =
                "growth-bars";


            const qualityBar =
                document.createElement(
                    "div"
                );

            qualityBar.className =
                "growth-quality";


            qualityBar.style.height =
                `${(quality / maxValue) * 100}%`;


            const optimizationBar =
                document.createElement(
                    "div"
                );

            optimizationBar.className =
                "growth-optimization";


            optimizationBar.style.height =
                `${(optimization / maxValue) * 100}%`;


            bars.appendChild(
                qualityBar
            );

            bars.appendChild(
                optimizationBar
            );


            const values =
                document.createElement(
                    "span"
                );

            values.className =
                "growth-values";


            values.textContent =
                `${quality.toFixed(0)} / ${optimization.toFixed(0)}`;


            point.appendChild(label);

            point.appendChild(bars);

            point.appendChild(values);

            container.appendChild(point);

        }
    );


    if (trend.length >= 2) {

        const first =
            Number(
                trend[0].quality || 0
            );

        const last =
            Number(
                trend[trend.length - 1].quality || 0
            );


        if (last > first) {

            status.textContent =
                "Improving ↑";

        }

        else if (last < first) {

            status.textContent =
                "Needs attention ↓";

        }

        else {

            status.textContent =
                "Stable →";

        }

    }

    else {

        status.textContent =
            "Building baseline";

    }

}


// =========================================================
// AI INSIGHTS
// =========================================================

function displayInsights(insights) {

    if (!insights) {
        return;
    }


    document.getElementById(
        "insightStrength"
    ).textContent =
        insights.strength ||
        "—";


    document.getElementById(
        "insightWeakness"
    ).textContent =
        insights.weakness ||
        "—";


    document.getElementById(
        "insightComplexity"
    ).textContent =
        insights.complexity ||
        "—";


    document.getElementById(
        "insightRecommendation"
    ).textContent =
        insights.recommendation ||
        "—";


    document.getElementById(
        "insightProgress"
    ).textContent =
        insights.progress ||
        "—";

}


// =========================================================
// CLUSTER
// =========================================================

function displayCluster(data) {

    const cluster =
        data.cluster;


    document.getElementById(
        "cluster"
    ).textContent =
        cluster !== null &&
            cluster !== undefined
            ? cluster
            : "—";

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


// =========================================================
// START
// =========================================================

loadProfile();