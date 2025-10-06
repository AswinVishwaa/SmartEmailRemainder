import os
import requests
import json
import re
import unicodedata
import time
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

MAX_BODY_LENGTH = 1000  # character limit to avoid too many tokens

def clean_llm_output(output):
    """
    Extract and parse JSON-like string from LLM response safely.
    Handles markdown code blocks and other artifacts.
    """
    try:
        normalized_output = unicodedata.normalize("NFKD", output)
        
        # Remove markdown code blocks if present
        normalized_output = re.sub(r'```(?:json|python)?\s*', '', normalized_output)
        normalized_output = re.sub(r'```', '', normalized_output)
        
        # Try to find JSON object
        match = re.search(r'\{[^{}]*"is_important"[^{}]*\}', normalized_output, re.DOTALL)
        if not match:
            # Fallback: find any JSON-like structure
            match = re.search(r'\{.*?\}', normalized_output, re.DOTALL)
            if not match:
                print("❌ No valid dictionary format found.")
                print(f"Raw output: {output[:200]}...")  # Debug print
                return None

        dict_str = match.group(0)
        
        # Replace Python booleans with JSON booleans
        dict_str = dict_str.replace('true', 'true').replace('false', 'false')
        dict_str = dict_str.replace('True', 'true').replace('False', 'false')
        
        return json.loads(dict_str)

    except json.JSONDecodeError as e:
        print(f"❌ JSON Parsing Error: {e}")
        print(f"Attempted to parse: {dict_str[:200]}...")  # Debug
        return None
    except Exception as e:
        print(f"❌ Unexpected error in clean_llm_output: {e}")
        return None


def process_email_with_llm(email_text, retries=5, delay=2.0):
    if not email_text or not email_text.strip():
        print("❌ Empty email text")
        return None
        
    safe_body = email_text.strip()[:MAX_BODY_LENGTH]
    safe_body = ''.join(char for char in safe_body if char.isprintable() or char.isspace())

    prompt = f"""
You are an assistant that processes and filters emails for WhatsApp notifications.
If the email is important (e.g., internship, interview, job offer, contest, OTP, etc.), return structured data.

CRITICAL: Respond ONLY with a valid JSON object. Do NOT include code, explanations, or markdown.

Required format:
{{
  "is_important": true,
  "title": "...",
  "deadline": "...",
  "action": "...",
  "summary": "..."
}}

If not important, set is_important to false.

Email:
\"\"\"{safe_body}\"\"\"

Remember: ONLY return the JSON object, nothing else.
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
    "model": "llama-3.1-8b-instant",
    "messages": [
        {"role": "system", "content": "You are an intelligent email summarizer. Always respond with valid JSON only."},
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.3,
    "response_format": {"type": "json_object"}  # Add this line
}

    for attempt in range(retries):
        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
            
            if res.status_code != 200:
                print(f"❌ Status Code: {res.status_code}")
                print(f"❌ Error Details: {res.text}")
                time.sleep(delay * (attempt + 1))
                continue

            content = res.json()["choices"][0]["message"]["content"]
            print("🧠 LLM Raw Output:\n", content[:300])  # Limit output length

            parsed = clean_llm_output(content)
            
            if parsed is None:
                print(f"⚠️ Failed to parse response, retrying... (Attempt {attempt + 1}/{retries})")
                time.sleep(1)
                continue  # Retry instead of returning None
                
            return parsed if parsed.get("is_important") else None

        except Exception as e:
            print(f"❌ Error: {e} (Attempt {attempt + 1}/{retries})")
            time.sleep(delay * (attempt + 1))

    print("❌ All retries failed.")
    return None