const API_URL = "https://aianalyser-4iaf.onrender.com";

const token =
    localStorage.getItem("access_token");


if (!token) {

    window.location.href =
        "login.html";
}


// =========================================================
// ELEMENTS
// =========================================================

const analyzeButton =
    document.getElementById(
        "analyzeButton"
    );

const message =
    document.getElementById(
        "message"
    );

const results =
    document.getElementById(
        "results"
    );

const codeEditor =
    document.getElementById("code");

const lineNumbers =
    document.getElementById("lineNumbers");


// =========================================================
// MESSAGE
// =========================================================

function showMessage(
    text,
    type = ""
) {

    message.textContent = text;

    message.className =
        `message ${type}`;
}


// =========================================================
// FORMAT
// =========================================================

function number(value) {

    return Number(value || 0)
        .toFixed(2);
}


function setScoreBar(id, value) {
    const safeValue =
        Math.max(
            0,
            Math.min(
                100,
                Number(value) || 0
            )
        );

    document.getElementById(id)
        .style.width =
        `${safeValue}%`;
}


function updateLineNumbers() {
    const lines =
        codeEditor.value.split("\n").length;

    lineNumbers.textContent =
        Array.from(
            { length: lines },
            (_, i) => i + 1
        ).join("\n");
}


codeEditor.addEventListener(
    "input",
    updateLineNumbers
);

codeEditor.addEventListener(
    "scroll",
    function () {
        lineNumbers.scrollTop =
            codeEditor.scrollTop;
    }
);

updateLineNumbers();


// =========================================================
// ANALYZE
// =========================================================

analyzeButton.addEventListener(
    "click",
    async function (event) {
        event.preventDefault();

        const code =
            document
                .getElementById("code")
                .value
                .trim();


        const problemName =
            document
                .getElementById("problemName")
                .value
                .trim() ||
            "Untitled Problem";


        if (!code) {

            showMessage(
                "Please enter some Python code.",
                "error"
            );

            return;
        }


        analyzeButton.disabled = true;

        analyzeButton.textContent =
            "Analyzing...";


        showMessage(
            "AI is analyzing your code..."
        );


        results.classList.add(
            "hidden"
        );


        try {

            const response =
                await fetch(
                    `${API_URL}/submissions/analyze`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json",

                            "Authorization":
                                `Bearer ${token}`
                        },

                        body: JSON.stringify({
                            code,
                            problem_name:
                                problemName
                        })
                    }
                );


            const data =
                await response.json();


            if (response.status === 401) {

                localStorage.clear();

                window.location.href =
                    "login.html";

                return;
            }


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Analysis failed."
                );

            }


            displayResults(data);


            showMessage(
                "Analysis complete.",
                "success"
            );

        }

        catch (error) {

            showMessage(
                error.message,
                "error"
            );

        }

        finally {

            analyzeButton.disabled =
                false;

            analyzeButton.textContent =
                "Analyze Code →";

        }

    }
);


// =========================================================
// DISPLAY RESULTS
// =========================================================

function displayResults(data) {

    const features =
        data.features;


    document.getElementById(
        "cluster"
    ).textContent =
        `Cluster ${data.cluster}`;


    document.getElementById(
        "complexity"
    ).textContent =
        number(
            features.average_complexity
        );


    document.getElementById(
        "maintainability"
    ).textContent =
        number(
            features.average_maintainability
        );


    document.getElementById(
        "optimization"
    ).textContent =
        number(
            features.optimization_score
        );

    document.getElementById(
        "emptyAnalysis"
    ).classList.add("hidden");

    document.getElementById(
        "previewResults"
    ).classList.remove("hidden");

    document.getElementById(
        "clusterConfidence"
    ).textContent =
        `${(data.cluster_memberships[data.cluster] * 100).toFixed(1)}% confidence`;

    document.getElementById(
        "quality"
    ).textContent =
        number(features.code_quality_score);

    document.getElementById(
        "optimizationLarge"
    ).textContent =
        number(features.optimization_score);

    document.getElementById(
        "algorithmLarge"
    ).textContent =
        number(features.algorithm_diversity);

    document.getElementById(
        "problemLarge"
    ).textContent =
        number(features.problem_solving_diversity);

    setScoreBar(
        "qualityBar",
        features.code_quality_score
    );

    setScoreBar(
        "optimizationBar",
        features.optimization_score
    );

    setScoreBar(
        "algorithmBar",
        features.algorithm_diversity
    );

    setScoreBar(
        "problemBar",
        features.problem_solving_diversity
    );


    document.getElementById(
        "algorithmDiversity"
    ).textContent =
        number(
            features.algorithm_diversity
        );


    document.getElementById(
        "dataStructureDiversity"
    ).textContent =
        number(
            features.data_structure_diversity
        );


    document.getElementById(
        "problemSolvingDiversity"
    ).textContent =
        number(
            features.problem_solving_diversity
        );


    document.getElementById(
        "bruteForce"
    ).textContent =
        number(
            features.brute_force_tendency
        );


    document.getElementById(
        "nestedLoops"
    ).textContent =
        `${number(
            features.nested_loop_percentage
        )}%`;


    document.getElementById(
        "recursion"
    ).textContent =
        `${number(
            features.recursion_percentage
        )}%`;


    displayProbabilities(
        data.cluster_memberships
    );


    results.classList.remove(
        "hidden"
    );


    results.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


// =========================================================
// CLUSTER PROBABILITIES
// =========================================================

function displayProbabilities(
    probabilities
) {

    const container =
        document.getElementById(
            "clusterProbabilities"
        );


    container.innerHTML = "";


    probabilities.forEach(
        function (probability, index) {

            const percentage =
                probability * 100;


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