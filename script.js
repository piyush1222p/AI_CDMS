const BASE_URL = "http://127.0.0.1:8000"; // Update this if backend is hosted elsewhere

document.addEventListener("DOMContentLoaded", () => {
    const languageSelect = document.getElementById("language");
    const codeTextarea = document.getElementById("code");
    const aiQueryTextarea = document.getElementById("ai-query");
    const runCodeButton = document.getElementById("run-code");
    const analyzeCodeButton = document.getElementById("analyze-code");
    const backendCodeTextarea = document.getElementById("backend-code");
    const backendQueryTextarea = document.getElementById("backend-query");
    const analyzeBackendCodeButton = document.getElementById("analyze-backend-code");
    const outputContent = document.getElementById("output-content");
    const aiFeedback = document.getElementById("ai-feedback");
    const backendFeedback = document.getElementById("backend-feedback");

    const runCode = async () => {
        const language = languageSelect.value;
        const code = codeTextarea.value;

        if (!language || !code) {
            alert("Please select a language and enter code.");
            return;
        }

        outputContent.textContent = "Processing...";
        try {
            const response = await fetch(`${BASE_URL}/check-code`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ language, code }),
            });
            const result = await response.json();

            if (response.ok) {
                outputContent.textContent = result.message || "Execution completed.";
            } else {
                outputContent.textContent = `Error: ${result.detail || "Unknown error."}`;
            }
        } catch (error) {
            outputContent.textContent = "Error: Unable to connect to the server.";
        }
    };

    const analyzeCode = async () => {
        const language = languageSelect.value;
        const code = codeTextarea.value;
        const query = aiQueryTextarea.value;

        if (!language || !code || !query) {
            alert("Please select a language, enter code, and provide a query for AI analysis.");
            return;
        }

        aiFeedback.textContent = "Analyzing with AI...";
        try {
            const response = await fetch(`${BASE_URL}/analyze-code`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ language, code, query }),
            });
            const result = await response.json();

            if (response.ok) {
                aiFeedback.textContent = result.feedback || "AI analysis completed.";
            } else {
                aiFeedback.textContent = `Error: ${result.detail || "Unknown error."}`;
            }
        } catch (error) {
            aiFeedback.textContent = "Error: Unable to connect to the server.";
        }
    };

    const analyzeBackendCode = async () => {
        const code = backendCodeTextarea.value;
        const query = backendQueryTextarea.value;

        if (!code || !query) {
            alert("Please enter backend code and a query for analysis.");
            return;
        }

        backendFeedback.textContent = "Analyzing backend code with AI...";
        try {
            const response = await fetch(`${BASE_URL}/analyze-backend-code`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code, query }),
            });
            const result = await response.json();

            if (response.ok) {
                backendFeedback.textContent = result.feedback || "Backend code analysis completed.";
            } else {
                backendFeedback.textContent = `Error: ${result.detail || "Unknown error."}`;
            }
        } catch (error) {
            backendFeedback.textContent = "Error: Unable to connect to the server.";
        }
    };

    runCodeButton.addEventListener("click", runCode);
    analyzeCodeButton.addEventListener("click", analyzeCode);
    analyzeBackendCodeButton.addEventListener("click", analyzeBackendCode);
});