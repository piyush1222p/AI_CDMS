import subprocess
import tempfile
import os

# Supported languages and their respective commands
SUPPORTED_LANGUAGES = {
    "python": "python",
    "javascript": "node",
    "c": "gcc",
    "cpp": "g++",
    "java": "javac",
}

def get_file_extension(language):
    """Return the appropriate file extension for the given language."""
    extensions = {
        "python": ".py",
        "javascript": ".js",
        "c": ".c",
        "cpp": ".cpp",
        "java": ".java",
    }
    return extensions.get(language, "")

def check_code(language, code):
    """Check the provided code for errors."""
    language = language.lower()

    # Check if the language is supported
    if language not in SUPPORTED_LANGUAGES:
        return f"Unsupported language. Supported languages are: {', '.join(SUPPORTED_LANGUAGES.keys())}"

    # Create a temporary file to store the code
    with tempfile.NamedTemporaryFile(suffix=get_file_extension(language), delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name

    try:
        if language in ["python", "javascript"]:
            # For interpreted languages, run the code
            result = subprocess.run(
                [SUPPORTED_LANGUAGES[language], temp_file_path],
                capture_output=True,
                text=True,
            )
        elif language in ["c", "cpp"]:
            # For compiled languages, compile the code
            compile_result = subprocess.run(
                [SUPPORTED_LANGUAGES[language], temp_file_path, "-o", temp_file_path + ".out"],
                capture_output=True,
                text=True,
            )
            if compile_result.returncode != 0:
                return f"Compilation Errors:\n{compile_result.stderr.strip()}"
            # Run the compiled executable
            result = subprocess.run(
                [temp_file_path + ".out"],
                capture_output=True,
                text=True,
            )
        elif language == "java":
            # Compile Java code
            compile_result = subprocess.run(
                [SUPPORTED_LANGUAGES[language], temp_file_path],
                capture_output=True,
                text=True,
            )
            if compile_result.returncode != 0:
                return f"Compilation Errors:\n{compile_result.stderr.strip()}"
            # Run the compiled Java class
            class_name = os.path.splitext(os.path.basename(temp_file_path))[0]
            result = subprocess.run(
                ["java", class_name],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(temp_file_path)  # Set the working directory
            )
        else:
            return "Unexpected error while processing the code."

    except FileNotFoundError as e:
        return f"Error: {e}\nMake sure the required interpreter or compiler is installed and available in your PATH."

    finally:
        # Clean up temporary files
        try:
            os.remove(temp_file_path)
            if language in ["c", "cpp"]:
                os.remove(temp_file_path + ".out")
            elif language == "java":
                os.remove(temp_file_path.replace(".java", ".class"))
        except Exception:
            pass  # Ignore cleanup errors

    # Return errors or output
    if result.stderr:
        return f"Errors:\n{result.stderr.strip()}"
    else:
        return f"Code executed successfully without errors.\nOutput:\n{result.stdout.strip()}"

# Main Function
if __name__ == "__main__":
    print("Welcome to the Local Code Checker!")
    print(f"Supported languages: {', '.join(SUPPORTED_LANGUAGES.keys())}\n")

    # Input for the programming language
    language = input("Enter the programming language: ").strip()

    # Input for the code (multi-line)
    print("\nEnter your code (press Enter on a blank line to finish):")
    code_lines = []
    while True:
        line = input()
        if line.strip() == "":  # End input on a blank line
            break
        code_lines.append(line)

    # Combine all lines into a single string
    code = "\n".join(code_lines)

    # Check for empty code
    if not code.strip():
        print("Error: No code was entered. Please try again.")
        exit()

    # Check the code
    result = check_code(language, code)
    print("\n" + "="*40 + "\n")
    print(result)