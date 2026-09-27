const API_URL = "http://127.0.0.1:8000";

const token = localStorage.getItem("access_token");

if (!token) {
    window.location.href = "login.html";
}


// =========================================================
// LOAD HISTORY
// =========================================================

async function loadHistory() {

    const historyList =
        document.getElementById("historyList");

    const emptyHistory =
        document.getElementById("emptyHistory");

    const message =
        document.getElementById("historyMessage");


    try {

        const response = await fetch(
            `${API_URL}/history/me`,
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
                "Unable to load history."
            );

        }


        const submissions =
            data.submissions || [];


        if (!submissions.length) {

            emptyHistory.classList.remove(
                "hidden"
            );

            return;
        }


        emptyHistory.classList.add(
            "hidden"
        );

        historyList.innerHTML = "";


        submissions
            .slice()
            .reverse()
            .forEach(
                submission => {

                    historyList.appendChild(
                        createSubmissionCard(
                            submission
                        )
                    );

                }
            );

    }

    catch (error) {

        message.textContent =
            error.message;

        message.className =
            "message error";

    }

}


// =========================================================
// CREATE HISTORY CARD
// =========================================================

function createSubmissionCard(
    submission
) {

    const card =
        document.createElement("article");

    card.className =
        "history-card";
    card.style.cursor = "pointer";
    card.addEventListener(
        "click",
        function () {
            window.location.href =
                `submission.html?id=${submission.id}`;
        }
    );


    const problem =
        submission.problem_name ||
        "Untitled Problem";


    const language =
        submission.language ||
        "Python";


    const cluster =
        submission.cluster !== null &&
        submission.cluster !== undefined
            ? submission.cluster
            : "—";


    const complexity =
        Number(
            submission.cyclomatic_complexity || 0
        ).toFixed(2);


    const quality =
        Number(
            submission.code_quality_score || 0
        ).toFixed(1);


    const optimization =
        Number(
            submission.optimization_score || 0
        ).toFixed(1);


    const algorithm =
        Number(
            submission.algorithm_diversity || 0
        ).toFixed(1);


    const dataStructure =
        Number(
            submission.data_structure_diversity || 0
        ).toFixed(1);


    const date =
        formatDate(
            submission.submitted_at
        );


    card.innerHTML = `

        <div class="history-main">

            <div class="history-title-row">

                <div class="history-code-icon">
                    PY
                </div>

                <div>

                    <h3>
                        ${escapeHtml(problem)}
                    </h3>

                    <span class="history-date">
                        ${date}
                    </span>

                </div>

            </div>


            <div class="history-meta">

                <span>
                    ${escapeHtml(language)}
                </span>

                <span>
                    Complexity ${complexity}
                </span>

                <span>
                    Quality ${quality}
                </span>

            </div>


            <div class="history-metrics">

                <div class="history-metric">

                    <span>
                        Optimization
                    </span>

                    <strong>
                        ${optimization}
                    </strong>

                </div>


                <div class="history-metric">

                    <span>
                        Algorithm
                    </span>

                    <strong>
                        ${algorithm}
                    </strong>

                </div>


                <div class="history-metric">

                    <span>
                        Data Structures
                    </span>

                    <strong>
                        ${dataStructure}
                    </strong>

                </div>

            </div>

        </div>


        <div class="history-cluster">

            <span>
                CLUSTER
            </span>

            <strong>
                ${cluster}
            </strong>

        </div>

    `;


    return card;

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
// HTML ESCAPING
// =========================================================

function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

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


loadHistory();