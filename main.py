from gmail_fetcher import fetch_emails
from llm_processor import process_email_with_llm
from whatsapp_bot import send_whatsapp_message, TO_WHATSAPP
import time
from context_store import load_context, save_context

def main():
    print("📬 Fetching latest emails...")
    emails = fetch_emails(4)
    sender_number = TO_WHATSAPP.replace("whatsapp:", "")
    context = load_context()

    if sender_number not in context:
        context[sender_number] = {}

    for index, email in enumerate(emails, start=1):
        body = email.get("body", "")
        if not body:
            continue

        parsed = process_email_with_llm(body)
        if not parsed:
            continue

        send_whatsapp_message(
            title=parsed.get("title", "No Title"),
            deadline=parsed.get("deadline", "N/A"),
            action=parsed.get("action", "N/A"),
            summary=parsed.get("summary", "N/A"),
            index=index
        )

        context[sender_number][str(index)] = {
            "summary": parsed.get("summary", ""),
            "title": parsed.get("title", ""),
            "deadline": parsed.get("deadline", ""),
            "action": parsed.get("action", ""),
            "original_body": body
        }

        time.sleep(1.2)

    save_context(context)

if __name__ == "__main__":
    main()
