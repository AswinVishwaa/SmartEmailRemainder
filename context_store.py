import json
import os

CONTEXT_FILE = "message_context.json"

def load_context():
    if not os.path.exists(CONTEXT_FILE):
        return {}
    try:
        with open(CONTEXT_FILE, "r") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        print("⚠️ Context file corrupted or empty. Reinitializing.")
        return {}

def save_context(context):
    with open(CONTEXT_FILE, "w") as f:
        json.dump(context, f, indent=2)
