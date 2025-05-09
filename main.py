from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os
from transformers import pipeline

# Initialize FastAPI app
app = FastAPI()

# CORS Middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supported Languages and Commands
SUPPORTED_LANGUAGES = {
    "python": "python",
    "javascript": "node",
    "c": "gcc",
    "cpp": "g++",
    "java": "javac",
}

# Load the Hugging Face GPT-2 model
generator = pipeline('text-generation', model='gpt2')

class CodeRequest(BaseModel):
    language: str
    code: str

class AIRequest(BaseModel):
    language: str
    code: str
    query: str

class BackendCodeRequest(BaseModel):
    code: str
    query: str  # Specific question or analysis request for the code


@app.post("/check-code")
async def check_code_endpoint(request: CodeRequest):
    """
    Endpoint to Execute Code and Return Output/Errors
    """
    try:
        response = await execute_code_async(request.language, request.code)
        return {"message": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-code")
async def analyze_code_with_ai_endpoint(request: AIRequest):
    """
    Endpoint to Analyze Code with AI and Provide Feedback
    """
    try:
        ai_feedback = await analyze_code(request.language, request.code, request.query)
        return {"feedback": ai_feedback}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-backend-code")
async def analyze_backend_code_endpoint(request: BackendCodeRequest):
    """
    Endpoint to analyze backend code and provide AI feedback.
    """
    try:
        ai_feedback = await analyze_code_with_ai(request.code, request.query)
        return {"feedback": ai_feedback}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def execute_code_async(language, code):
    """
    Executes the provided code asynchronously and returns the output or errors.
    """
    language = language.lower()
    if language not in SUPPORTED_LANGUAGES:
        return f"Unsupported language. Supported languages: {', '.join(SUPPORTED_LANGUAGES.keys())}"

    # Create a temporary file for the code
    file_extension = get_file_extension(language)
    temp_file = f"temp_code{file_extension}"
    with open(temp_file, "w") as f:
        f.write(code)

    try:
        # Execute the code asynchronously
        if language in ["python", "javascript"]:
            process = await asyncio.create_subprocess_exec(
                SUPPORTED_LANGUAGES[language],
                temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        elif language in ["c", "cpp"]:
            compile_command = [SUPPORTED_LANGUAGES[language], temp_file, "-o", "temp.out"]
            compile_process = await asyncio.create_subprocess_exec(
                *compile_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            compile_stdout, compile_stderr = await compile_process.communicate()

            if compile_process.returncode != 0:
                return f"Compilation Error:\n{compile_stderr.decode()}"

            process = await asyncio.create_subprocess_exec(
                "./temp.out",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        elif language == "java":
            compile_command = [SUPPORTED_LANGUAGES[language], temp_file]
            compile_process = await asyncio.create_subprocess_exec(
                *compile_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            compile_stdout, compile_stderr = await compile_process.communicate()

            if compile_process.returncode != 0:
                return f"Compilation Error:\n{compile_stderr.decode()}"

            class_name = os.path.splitext(os.path.basename(temp_file))[0]
            process = await asyncio.create_subprocess_exec(
                "java",
                "-cp",
                ".",
                class_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        else:
            return "Unexpected error occurred while processing the code."

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            return f"Runtime Error:\n{stderr.decode()}"
        else:
            return f"Code executed successfully.\nOutput:\n{stdout.decode()}"
    finally:
        # Clean up temporary files
        try:
            os.remove(temp_file)
            if language in ["c", "cpp"]:
                os.remove("temp.out")
            elif language == "java":
                os.remove(temp_file.replace(".java", ".class"))
        except Exception:
            pass  # Ignore errors during cleanup


async def analyze_code(language, code, query):
    """
    Uses AI to analyze code and provide feedback.
    """
    prompt = f"""
    Analyze the following {language} code and answer the query: "{query}"

    Code:
    {code}
    """
    try:
        # Use the Hugging Face model to generate a response
        response = generator(prompt, max_length=500, num_return_sequences=1)
        return response[0]['generated_text']
    except Exception as e:
        return f"AI Analysis Error: {str(e)}"


async def analyze_code_with_ai(code: str, query: str) -> str:
    """
    Uses AI to analyze the backend code and provide AI feedback.
    """
    prompt = f"""
    You are an expert backend developer and code reviewer. Analyze the following backend code and answer the query: "{query}".

    Code:
    {code}
    """
    try:
        # Generate a response using the Hugging Face model
        response = generator(prompt, max_length=500, num_return_sequences=1)
        return response[0]['generated_text']
    except Exception as e:
        return f"Error analyzing code: {str(e)}"


def get_file_extension(language):
    """
    Get the file extension for a given programming language.
    """
    extensions = {
        "python": ".py",
        "javascript": ".js",
        "c": ".c",
        "cpp": ".cpp",
        "java": ".java",
    }
    return extensions.get(language, "")