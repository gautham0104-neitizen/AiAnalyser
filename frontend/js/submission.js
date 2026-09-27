const API_URL = "https://aianalyser-4iaf.onrender.com";

const token =
    localStorage.getItem("access_token");

if (!token) {
    window.location.href = "login.html";
}


// =========================================================
// SUBMISSION ID
// =========================================================

const params =
    new URLSearchParams(
        window.location.search
    );

const submissionId =
    params.get("id");


if (!submissionId) {

    window.location.href =
        "history.html";
}


// =========================================================
// ELEMENTS
// =========================================================

const message =
    document.getElementById("message");


// =========================================================
// HELPERS
// =========================================================

function number(value) {

    return Number(value || 0)
        .toFixed(2);

}


function showMessage(
    text,
    type = ""
) {

    message.textContent = text;

    message.className =
        `message ${type}`;

}


// =========================================================
// LOAD SUBMISSION
// =========================================================

async function loadSubmission() {

    try {

        const response =
            await fetch(
                `${API_URL}/submissions/${submissionId}`,
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
                "Unable to load submission."
            );

        }


        displaySubmission(data);

    }

    catch (error) {

        showMessage(
            error.message,
            "error"
        );

    }

}


// =========================================================
// DISPLAY SUBMISSION
// =========================================================

function displaySubmission(data) {

    document.getElementById(
        "problemName"
    ).textContent =
        data.problem_name ||
        "Untitled Problem";


    document.getElementById(
        "submissionMeta"
    ).textContent =
        `${data.language || "Python"} · ${formatDate(data.submitted_at)}`;


    document.getElementById(
        "quality"
    ).textContent =
        number(
            data.code_quality_score
        );


    document.getElementById(
        "optimization"
    ).textContent =
        number(
            data.optimization_score
        );


    document.getElementById(
        "complexity"
    ).textContent =
        number(
            data.cyclomatic_complexity
        );


    document.getElementById(
        "cluster"
    ).textContent =
        data.cluster !== null &&
        data.cluster !== undefined
            ? `Cluster ${data.cluster}`
            : "—";


    // -----------------------------------------------------
    // BEHAVIOR
    // -----------------------------------------------------

    document.getElementById(
        "algorithm"
    ).textContent =
        number(
            data.algorithm_diversity
        );


    document.getElementById(
        "dataStructure"
    ).textContent =
        number(
            data.data_structure_diversity
        );


    document.getElementById(
        "problemSolving"
    ).textContent =
        number(
            data.problem_solving_diversity
        );


    document.getElementById(
        "bruteForce"
    ).textContent =
        number(
            data.brute_force_tendency
        );


    document.getElementById(
        "nestedLoops"
    ).textContent =
        `${number(data.nested_loop_percentage)}%`;


    document.getElementById(
        "recursion"
    ).textContent =
        `${number(data.recursion_percentage)}%`;


    // -----------------------------------------------------
    // CODE
    // -----------------------------------------------------

    document.getElementById(
        "submittedCode"
    ).textContent =
        data.code || "";


    // -----------------------------------------------------
    // TECHNICAL DETAILS
    // -----------------------------------------------------

    document.getElementById(
        "loc"
    ).textContent =
        data.loc;


    document.getElementById(
        "maintainability"
    ).textContent =
        number(
            data.maintainability_index
        );


    document.getElementById(
        "functions"
    ).textContent =
        data.num_functions;


    document.getElementById(
        "classes"
    ).textContent =
        data.num_classes;


    document.getElementById(
        "loops"
    ).textContent =
        data.total_loops;


    document.getElementById(
        "maxComplexity"
    ).textContent =
        number(
            data.maximum_cyclomatic_complexity
        );


    // -----------------------------------------------------
    // CLUSTER PROBABILITIES
    // -----------------------------------------------------

    displayProbabilities(
        data.cluster_memberships
    );

    displayExplanation(
        data.explanation
    );

}


// =========================================================
// CLUSTER PROBABILITIES
// =========================================================

function displayProbabilities(
    value
) {

    const container =
        document.getElementById(
            "clusterProbabilities"
        );

    container.innerHTML = "";


    let probabilities;


    try {

        probabilities =
            typeof value === "string"
                ? JSON.parse(value)
                : value;

    }

    catch {

        probabilities = [];

    }


    if (!Array.isArray(probabilities)) {
        return;
    }


    probabilities.forEach(
        function (
            probability,
            index
        ) {

            const percentage =
                Number(probability) * 100;


            const row =
                document.createElement(
                    "div"
                );

            row.className =
                "probability-row";


            row.innerHTML = `

                <span>
                    Cluster ${index}
                </span>

                <div class="probability-track">

                    <div
                        class="probability-fill"
                        style="width: ${percentage}%"
                    ></div>

                </div>

                <strong>
                    ${percentage.toFixed(1)}%
                </strong>

            `;


            container.appendChild(row);

        }
    );

}


// =========================================================
// DATE
// =========================================================

function formatDate(value) {

    if (!value) {
        return "Unknown date";
    }


    const date =
        new Date(
            value.replace(" ", "T")
        );


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return value;

    }


    return date.toLocaleDateString(
        undefined,
        {
            day: "numeric",
            month: "short",
            year: "numeric"
        }
    );

}


// =========================================================
// EXPLAINABLE ANALYSIS
// =========================================================

function displayExplanation(explanation) {

    if (!explanation) {
        return;
    }

    // -----------------------------------------------------
    // DETECTED APPROACH
    // -----------------------------------------------------

    if (
        explanation.approach &&
        explanation.approach.approaches
    ) {

        const approaches =
            document.getElementById(
                "detectedApproaches"
            );

        approaches.innerHTML = "";

        explanation.approach.approaches.forEach(
            function (approach) {

                const tag =
                    document.createElement(
                        "span"
                    );

                tag.className =
                    "explanation-tag";

                tag.textContent =
                    approach;

                approaches.appendChild(tag);

            }
        );

    }

    // -----------------------------------------------------
    // COMPLEXITY
    // -----------------------------------------------------

    if (explanation.complexity) {

        document.getElementById(
            "explanationComplexityScore"
        ).textContent =
            Number(
                explanation.complexity.score || 0
            ).toFixed(2);

        document.getElementById(
            "complexityExplanation"
        ).textContent =
            explanation.complexity.explanation ||
            "No complexity explanation available.";

    }

    // -----------------------------------------------------
    // OPTIMIZATION
    // -----------------------------------------------------

    if (explanation.optimization) {

        document.getElementById(
            "explanationOptimizationScore"
        ).textContent =
            Number(
                explanation.optimization.score || 0
            ).toFixed(1);

        document.getElementById(
            "optimizationExplanation"
        ).textContent =
            explanation.optimization.explanation ||
            "No optimization explanation available.";

    }

    // -----------------------------------------------------
    // QUALITY
    // -----------------------------------------------------

    if (explanation.quality) {

        document.getElementById(
            "explanationQualityScore"
        ).textContent =
            Number(
                explanation.quality.score || 0
            ).toFixed(1);

        document.getElementById(
            "qualityExplanation"
        ).textContent =
            explanation.quality.explanation ||
            "No quality explanation available.";

    }

    // -----------------------------------------------------
    // IMPROVEMENT
    // -----------------------------------------------------

    document.getElementById(
        "improvementSuggestion"
    ).textContent =
        explanation.improvement ||
        "No improvement suggestion available.";

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


loadSubmission();