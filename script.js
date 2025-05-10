const BASE_URL = "http://127.0.0.1:8000"; // Update this if backend is hosted elsewhere

document.addEventListener("DOMContentLoaded", () => {
    const languageSelect = document.getElementById("language");
    const codeTextarea = document.getElementById("code");
    const aiQueryTextarea = document.getElementById("query");
    const runCodeButton = document.getElementById("run-code");
    const analyzeCodeButton = document.getElementById("analyze-code");
    const outputContent = document.getElementById("output-content");
    const aiFeedback = document.getElementById("ai-feedback");
    const programInput = document.getElementById("program-input"); // new input element

    const runCode = async () => {
        const language = languageSelect.value;
        const code = codeTextarea.value;
        const user_input = programInput.value; // get the program input value

        if (!language || !code) {
            alert("Please select a language and enter code.");
            return;
        }

        outputContent.textContent = "Processing...";
        try {
            const response = await fetch(`${BASE_URL}/check-code`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ language, code, user_input }), // send user_input to backend
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

    runCodeButton.addEventListener("click", runCode);
    analyzeCodeButton.addEventListener("click", analyzeCode);
});