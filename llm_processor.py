import os
import requests
import json
import re
import unicodedata
import time
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq") # "groq" or "gemini"

# Groq Config
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Gemini Config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

MAX_BODY_LENGTH = 1000

def clean_llm_output(output):
    """
    Extract and parse JSON-like string from LLM response safely.
    """
    try:
        normalized_output = unicodedata.normalize("NFKD", output)
        normalized_output = re.sub(r'```(?:json|python)?\s*', '', normalized_output)
        normalized_output = re.sub(r'```', '', normalized_output)
        
        match = re.search(r'\{[^{}]*"is_important"[^{}]*\}', normalized_output, re.DOTALL)
        if not match:
            match = re.search(r'\{.*?\}', normalized_output, re.DOTALL)
            if not match:
                return None

        dict_str = match.group(0)
        dict_str = dict_str.replace('true', 'true').replace('false', 'false') # Safety
        return json.loads(dict_str)

    except Exception as e:
        print(f"❌ JSON Parsing Error: {e}")
        return None

def call_llm(messages, json_mode=False):
    """
    Unified function to call either Groq or Gemini
    """
    if LLM_PROVIDER == "gemini":
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Convert OpenAI "messages" format to Gemini "history" format (simplified)
        prompt = messages[-1]['content'] # Just taking the last user prompt for simplicity in this context
        
        try:
            if json_mode:
                response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            else:
                response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"❌ Gemini Error: {e}")
            return None

    else: # Default to Groq
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": messages,
            "temperature": 0.3
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
            if res.status_code != 200:
                print(f"❌ Groq Error: {res.text}")
                return None
            return res.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"❌ Groq Connection Error: {e}")
            return None


def process_email_with_llm(email_text, retries=3):
    safe_body = email_text.strip()[:MAX_BODY_LENGTH]
    
    current_time_str = time.strftime("%Y-%m-%d %H:%M:%S")

    prompt = f"""
    You are an assistant that processes emails.
    Current Date/Time: {current_time_str}

    If the email is important (internship, interview, job offer, etc.), return valid JSON.

    CRITICAL: Respond ONLY with a valid JSON object.
    1. "deadline": EXTRACT the exact deadline if present. CONVERT relative dates (e.g., 'next Friday') to absolute ISO 8601 (YYYY-MM-DD HH:MM:SS) based on the Current Date. If none, return null.

    Required format:
    {{
      "is_important": true,
      "title": "...",
      "deadline": "YYYY-MM-DD HH:MM:SS",
      "action": "...",
      "summary": "..."
    }}

    Email:
    \"\"\"{safe_body}\"\"\"
    """

    messages = [
        {"role": "system", "content": "You are an intelligent email summarizer. Always respond with valid JSON only."},
        {"role": "user", "content": prompt}
    ]

    for _ in range(retries):
        content = call_llm(messages, json_mode=True)
        if content:
            parsed = clean_llm_output(content)
            if parsed:
                return parsed if parsed.get("is_important") else None
        time.sleep(1)
        
    return None

def classify_intent(user_input):
    prompt = f"""
    Classify the user input:
    1. DRAFT (User wants a reply written)
    2. QUESTION (User asks for info)
    3. SEND (User confirms sending)
    4. CANCEL (User stops action)
    
    User Input: "{user_input}"
    Return JSON: {{"intent": "DRAFT" | "QUESTION" | "SEND" | "CANCEL"}}
    """
    
    messages = [{"role": "user", "content": prompt}]
    content = call_llm(messages, json_mode=True)
    if content:
        try:
            return json.loads(content).get("intent", "QUESTION")
        except:
            return "QUESTION"
    return "QUESTION"

def chat_with_email(email_body, question):
    prompt = f"""
    Context:
    \"\"\"{email_body[:2000]}\"\"\"
    
    Question: "{question}"
    
    Answer concisely.
    """
    messages = [{"role": "user", "content": prompt}]
    return call_llm(messages) or "Sorry, I couldn't process that."