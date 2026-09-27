const API_URL = "https://aianalyser-4iaf.onrender.com";


function showMessage(
    message,
    type
) {

    const element =
        document.getElementById("message");

    if (!element) {
        return;
    }

    element.textContent = message;

    element.className =
        `message ${type}`;
}


// =========================================================
// LOGIN
// =========================================================

const loginForm =
    document.getElementById("loginForm");


if (loginForm) {

    loginForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            const username =
                document
                    .getElementById("username")
                    .value
                    .trim();

            const password =
                document
                    .getElementById("password")
                    .value;


            showMessage(
                "Logging in...",
                ""
            );


            try {

                const response =
                    await fetch(
                        `${API_URL}/auth/login`,
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                username,
                                password
                            })
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.detail ||
                        "Login failed."
                    );

                }


                localStorage.setItem(
                    "access_token",
                    data.access_token
                );


                localStorage.setItem(
                    "username",
                    data.username
                );


                localStorage.setItem(
                    "user_id",
                    data.user_id
                );


                showMessage(
                    "Login successful.",
                    "success"
                );


                setTimeout(
                    function () {

                        window.location.href =
                            "dashboard.html";

                    },
                    500
                );

            }

            catch (error) {

                showMessage(
                    error.message,
                    "error"
                );

            }

        }
    );

}


// =========================================================
// REGISTER
// =========================================================

const registerForm =
    document.getElementById(
        "registerForm"
    );


if (registerForm) {

    registerForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const username =
                document
                    .getElementById("username")
                    .value
                    .trim();

            const password =
                document
                    .getElementById("password")
                    .value;

            const confirmPassword =
                document
                    .getElementById("confirmPassword")
                    .value;


            if (
                password !==
                confirmPassword
            ) {

                showMessage(
                    "Passwords do not match.",
                    "error"
                );

                return;
            }


            showMessage(
                "Creating account...",
                ""
            );


            try {

                const response =
                    await fetch(
                        `${API_URL}/auth/register`,
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                username,
                                password
                            })
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.detail ||
                        "Registration failed."
                    );

                }


                showMessage(
                    "Account created! Redirecting to login...",
                    "success"
                );


                setTimeout(
                    function () {

                        window.location.href =
                            "login.html";

                    },
                    1000
                );

            }

            catch (error) {

                showMessage(
                    error.message,
                    "error"
                );

            }

        }
    );

}