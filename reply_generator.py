from llm_processor import call_llm

def generate_reply(email_text, instruction="Reply professionally"):
    prompt = f"""
You are an assistant that helps generate polite email replies.

Original email:
\"\"\"{email_text}\"\"\"

User Instruction: "{instruction}"

Write a professional email reply based on the user's instruction. Do not include placeholders like "[Your Name]". just the body.
"""

    messages = [
        {"role": "system", "content": "You generate polite and effective email replies."},
        {"role": "user", "content": prompt}
    ]

    try:
        reply = call_llm(messages)
        if reply:
            return reply.strip()
        return "❌ Error: LLM returned empty reply."
    except Exception as e:
        return f"❌ Error generating reply: {e}"
