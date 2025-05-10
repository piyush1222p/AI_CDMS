import sys
import asyncio
import os
import tempfile
import traceback
import logging
import shutil
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPPORTED_LANGUAGES = {
    "python": sys.executable,
    "cpp": "g++",
    "java": "javac",
}

# Ollama model you want to use
OLLAMA_MODEL = "mistral"  # Change this to e.g. "llama2" or "phi3" if you want a different model

class CodeRequest(BaseModel):
    language: str
    code: str
    user_input: str = ""

class AIRequest(BaseModel):
    language: str
    code: str
    query: str

class BackendCodeRequest(BaseModel):
    code: str
    query: str

class LocalAnalyzeRequest(BaseModel):
    code: str
    query: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/check-code")
async def check_code_endpoint(request: CodeRequest):
    try:
        if not request.language or not request.code.strip():
            raise HTTPException(status_code=400, detail="Language and code must be provided.")

        response = await execute_code_async(request.language, request.code, request.user_input)
        return {"message": response}
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error("Traceback: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="An unknown error occurred.")

def ollama_model_exists(model_name: str) -> bool:
    try:
        tags_resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if tags_resp.status_code == 200:
            tags = tags_resp.json().get("models", [])
            return any(m.get("name", "") == model_name for m in tags)
    except Exception as e:
        logger.error(f"Error checking Ollama model: {str(e)}")
    return False

def ollama_generate(prompt: str, model: str = OLLAMA_MODEL):
    if not ollama_model_exists(model):
        raise HTTPException(
            status_code=400,
            detail=f'Ollama model "{model}" is not available. '
                   f'Please run `ollama run {model}` or pull it first.'
        )
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt}
        )
        if response.status_code == 200 and 'response' in response.json():
            return response.json()['response'].strip()
        return f"Error from local AI model: {response.text}"
    except Exception as e:
        return f"Error communicating with local AI model: {str(e)}"

@app.post("/analyze-code")
def analyze_code_with_ai_endpoint(request: AIRequest):
    if not request.language or not request.code.strip() or not request.query.strip():
        raise HTTPException(status_code=400, detail="Language, code, and query must be provided.")

    prompt = (
        f"Analyze the following {request.language} code and answer the query: \"{request.query}\"\n\n"
        f"Code:\n{request.code}\n"
    )
    feedback = ollama_generate(prompt)
    return {"feedback": feedback}

@app.post("/analyze-backend-code")
def analyze_backend_code_endpoint(request: BackendCodeRequest):
    if not request.code.strip() or not request.query.strip():
        raise HTTPException(status_code=400, detail="Code and query must be provided.")

    prompt = (
        f"You are an expert backend developer and code reviewer. "
        f"Analyze the following backend code and answer the query: \"{request.query}\".\n\n"
        f"Code:\n{request.code}\n"
    )
    feedback = ollama_generate(prompt)
    return {"feedback": feedback}

@app.post("/analyze-code-local")
def analyze_code_local(request: LocalAnalyzeRequest):
    prompt = (
        f"Analyze the following code and answer the query: \"{request.query}\"\n\n"
        f"Code:\n{request.code}\n"
    )
    feedback = ollama_generate(prompt)
    return {"feedback": feedback}

async def execute_code_async(language, code, user_input=""):
    language = language.lower()
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")

    temp_dir = tempfile.mkdtemp()
    file_ext = get_file_extension(language)
    try:
        if language == "java":
            class_name = extract_java_class_name(code)
            if not class_name:
                shutil.rmtree(temp_dir)
                return "Error: Could not detect a public class in your Java code."
            temp_file_path = os.path.join(temp_dir, f"{class_name}.java")
            with open(temp_file_path, "w", encoding="utf-8") as temp_file:
                temp_file.write(code)
            try:
                compile_proc = await asyncio.create_subprocess_exec(
                    "javac", temp_file_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=temp_dir,
                )
                c_stdout, c_stderr = await compile_proc.communicate()
                if compile_proc.returncode != 0:
                    return f"Compilation Error:\n{c_stderr.decode()}"
            except FileNotFoundError:
                return "Java compiler (javac) not found. Please install Java JDK."
            try:
                run_proc = await asyncio.create_subprocess_exec(
                    "java", class_name,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=temp_dir,
                )
                r_stdout, r_stderr = await run_proc.communicate(input=user_input.encode() if user_input else None)
                if run_proc.returncode != 0:
                    return f"Runtime Error:\n{r_stderr.decode()}"
                else:
                    return r_stdout.decode()
            except FileNotFoundError:
                return "Java runtime (java) not found. Please install Java JDK."
        else:
            temp_file_path = os.path.join(temp_dir, f"main{file_ext}")
            with open(temp_file_path, "w", encoding="utf-8") as temp_file:
                temp_file.write(code)

            if not os.path.exists(temp_file_path):
                raise HTTPException(status_code=500, detail="Temporary file not found.")

            if language == "python":
                command = [sys.executable, temp_file_path]
                proc = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.PIPE,
                    cwd=temp_dir,
                )
                stdout, stderr = await proc.communicate(input=user_input.encode() if user_input else None)
                if proc.returncode != 0:
                    return f"Runtime Error:\n{stderr.decode()}"
                else:
                    return f"{stdout.decode()}"

            elif language == "cpp":
                exe_path = os.path.join(temp_dir, "a.exe" if sys.platform == "win32" else "a.out")
                compile_proc = await asyncio.create_subprocess_exec(
                    "g++", temp_file_path, "-o", exe_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=temp_dir,
                )
                c_stdout, c_stderr = await compile_proc.communicate()
                if compile_proc.returncode != 0:
                    return f"Compilation Error:\n{c_stderr.decode()}"
                run_proc = await asyncio.create_subprocess_exec(
                    exe_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.PIPE,
                    cwd=temp_dir,
                )
                r_stdout, r_stderr = await run_proc.communicate(input=user_input.encode() if user_input else None)
                if run_proc.returncode != 0:
                    return f"Runtime Error:\n{r_stderr.decode()}"
                else:
                    return f"{r_stdout.decode()}"
            else:
                return "Language not supported yet."
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def get_file_extension(language):
    extensions = {
        "python": ".py",
        "cpp": ".cpp",
        "java": ".java",
    }
    return extensions.get(language, "")

def extract_java_class_name(code):
    import re
    match = re.search(r'public\s+class\s+([A-Za-z_][A-Za-z0-9_]*)', code)
    return match.group(1) if match else None