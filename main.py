import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import tempfile
from transformers import pipeline, Pipeline
import traceback
import logging
import shutil

# Configure logging
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

try:
    generator: Pipeline = pipeline('text-generation', model='gpt2')
    logger.info("GPT-2 model loaded successfully.")
except Exception as e:
    logger.error(f"Error loading GPT-2 model: {e}")

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

@app.post("/analyze-code")
async def analyze_code_with_ai_endpoint(request: AIRequest):
    try:
        if not request.language or not request.code.strip() or not request.query.strip():
            raise HTTPException(status_code=400, detail="Language, code, and query must be provided.")

        ai_feedback = await analyze_code(request.language, request.code, request.query)
        return {"feedback": ai_feedback}
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error("Traceback: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="An unknown error occurred.")

@app.post("/analyze-backend-code")
async def analyze_backend_code_endpoint(request: BackendCodeRequest):
    try:
        if not request.code.strip() or not request.query.strip():
            raise HTTPException(status_code=400, detail="Code and query must be provided.")

        ai_feedback = await analyze_code_with_ai(request.code, request.query)
        return {"feedback": ai_feedback}
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error("Traceback: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="An unknown error occurred.")

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

async def analyze_code(language, code, query):
    prompt = f"""
    Analyze the following {language} code and answer the query: "{query}"

    Code:
    {code}
    """
    try:
        response = generator(prompt, max_length=500, num_return_sequences=1)
        return response[0]['generated_text']
    except Exception as e:
        return f"AI Analysis Error: {str(e)}"

async def analyze_code_with_ai(code: str, query: str) -> str:
    prompt = f"""
    You are an expert backend developer and code reviewer. Analyze the following backend code and answer the query: "{query}".

    Code:
    {code}
    """
    try:
        response = generator(prompt, max_length=500, num_return_sequences=1)
        return response[0]['generated_text']
    except Exception as e:
        return f"Error analyzing code: {str(e)}"

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