# reply_generator.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def generate_reply(email_text, instruction="Reply professionally"):
    prompt = f"""
You are an assistant that helps generate polite email replies.

Original email:
\"\"\"{email_text}\"\"\"

User Instruction: "{instruction}"

Write a professional email reply based on the user's instruction. Do not include placeholders like "[Your Name]". just the body.
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You generate polite and effective email replies."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4
    }

    try:
        res = requests.post(GROQ_API_URL, headers=headers, json=payload)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"❌ Error generating reply: {e}"
