import os
from dotenv import load_dotenv
import openai

load_dotenv()  # This loads variables from .env into environment

openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_code_with_ai(code, query, model="gpt-3.5-turbo"):
    messages = [
        {"role": "system", "content": "You are a helpful assistant who explains code."},
        {"role": "user", "content": f"{query}\n\n{code}"}
    ]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        max_tokens=512,
        temperature=0.5,
    )
    return response['choices'][0]['message']['content']