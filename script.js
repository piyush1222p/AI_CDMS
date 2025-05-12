const BASE_URL = "http://127.0.0.1:8000"; // Update this if backend is hosted elsewhere

document.addEventListener("DOMContentLoaded", () => {
    const languageSelect = document.getElementById("language");
    const codeTextarea = document.getElementById("code");
    const runCodeButton = document.getElementById("run-code");
    const outputContent = document.getElementById("output-content");
    const programInput = document.getElementById("program-input");

    // Version control elements
    const gitCloneBtn = document.getElementById("git-clone-btn");
    const gitPullBtn = document.getElementById("git-pull-btn");
    const gitCommitPushBtn = document.getElementById("git-commit-push-btn");
    const gitRepoUrl = document.getElementById("git-repo-url");
    const gitLocalPath = document.getElementById("git-local-path");
    const gitCommitMsg = document.getElementById("git-commit-msg");
    const gitBranch = document.getElementById("git-branch");
    const gitOutput = document.getElementById("git-output");

    const runCode = async () => {
        const language = languageSelect.value;
        const code = codeTextarea.value;
        const user_input = programInput.value;

        if (!language || !code) {
            alert("Please select a language and enter code.");
            return;
        }

        outputContent.textContent = "Processing...";
        try {
            const response = await fetch(`${BASE_URL}/check-code`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ language, code, user_input }),
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

    // --- Version Control Functions ---

    const gitClone = async () => {
        const repo_url = gitRepoUrl.value;
        const local_path = gitLocalPath.value;
        if (!repo_url || !local_path) {
            alert("Please enter both repository URL and local path.");
            return;
        }
        gitOutput.textContent = "Cloning repository...";
        try {
            const response = await fetch(`${BASE_URL}/git/clone`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ repo_url, local_path }),
            });
            const result = await response.json();
            gitOutput.textContent = response.ok
                ? result.message
                : `Error: ${result.detail || "Unknown error."}`;
        } catch (error) {
            gitOutput.textContent = "Error: Unable to connect to the server.";
        }
    };

    const gitPull = async () => {
        const local_path = gitLocalPath.value;
        if (!local_path) {
            alert("Please enter the local path.");
            return;
        }
        gitOutput.textContent = "Pulling repository...";
        try {
            const response = await fetch(`${BASE_URL}/git/pull`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ local_path }),
            });
            const result = await response.json();
            gitOutput.textContent = response.ok
                ? result.message
                : `Error: ${result.detail || "Unknown error."}`;
        } catch (error) {
            gitOutput.textContent = "Error: Unable to connect to the server.";
        }
    };

    const gitCommitPush = async () => {
        const local_path = gitLocalPath.value;
        const commit_message = gitCommitMsg.value;
        const branch = gitBranch.value || "main";
        if (!local_path || !commit_message) {
            alert("Please enter the local path and commit message.");
            return;
        }
        gitOutput.textContent = "Committing and pushing changes...";
        try {
            const response = await fetch(`${BASE_URL}/git/commit-push`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ local_path, commit_message, branch }),
            });
            const result = await response.json();
            gitOutput.textContent = response.ok
                ? result.message
                : `Error: ${result.detail || "Unknown error."}`;
        } catch (error) {
            gitOutput.textContent = "Error: Unable to connect to the server.";
        }
    };

    // --- Event listeners ---
    runCodeButton.addEventListener("click", runCode);

    if (gitCloneBtn) gitCloneBtn.addEventListener("click", gitClone);
    if (gitPullBtn) gitPullBtn.addEventListener("click", gitPull);
    if (gitCommitPushBtn) gitCommitPushBtn.addEventListener("click", gitCommitPush);
});