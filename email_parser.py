# email_parser.py
import re
from datetime import datetime, timedelta

# Simple keywords to categorize email
CATEGORY_KEYWORDS = {
    "internship": ["internship", "intern", "apply", "opening"],
    "job": ["job", "career", "opportunity", "position"],
    "event": ["event", "webinar", "session", "workshop"],
    "meeting": ["meeting", "zoom", "google meet", "calendar"],
    "interview": ["interview", "shortlisted", "selection"],
}

def extract_category(body):
    body_lower = body.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in body_lower:
                return category
    return "general"

def extract_dates(text):
    """Extracts dates like 'June 30', '30 June', '2025-06-30', etc."""
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # 30/06/2025 or 30-06-2025
        r'\b(?:\d{1,2}\s)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,]*(?:\d{2,4})?\b',  # 30 June or June 30, 2025
        r'\b\d{4}-\d{2}-\d{2}\b',  # ISO format: 2025-06-30
    ]
    matches = []
    for pattern in date_patterns:
        matches.extend(re.findall(pattern, text, re.IGNORECASE))
    return matches

def summarize_email(subject, body):
    summary = subject if len(subject) < 80 else subject[:80] + "..."
    body_snippet = body.strip().replace('\n', ' ')[:100]
    return f"{summary} – {body_snippet}"

def parse_email(email):
    subject = email.get('subject', '')
    body = email.get('body', '')

    dates = extract_dates(subject + " " + body)
    category = extract_category(subject + " " + body)
    summary = summarize_email(subject, body)

    return {
        "summary": summary,
        "category": category,
        "dates": dates or ["No date found"]
    }
