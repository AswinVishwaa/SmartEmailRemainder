from gmail_fetcher import fetch_emails
from llm_processor import process_email_with_llm
from whatsapp_bot import send_whatsapp_message, TO_WHATSAPP
from context_store import load_context, save_context, check_if_processed, mark_as_processed
import time
import os

def process_new_emails():
    """
    Fetches emails, uses LLM to identify actionable ones, and notifies via WhatsApp.
    """
    print("📬 Polling for new emails...")
    
    # In a real daemon, we'd track "last_checked_id" to avoid duplicates.
    # For now, we fetch latest 3 distinct emails.
    emails = fetch_emails(3)
    
    if not emails:
        print("No new emails found.")
        return

    # Determine Sender Number
    if TO_WHATSAPP:
        sender_number = TO_WHATSAPP.replace("whatsapp:", "").replace("+", "")
    else:
        return

    context = load_context()
    if sender_number not in context:
        context[sender_number] = {}
    
    processed_count = 0

    for index, email in enumerate(emails, start=1):
        msg_id = email.get("id")
        
        # 1. Check DB Cache (Avoid re-processing known emails)
        if check_if_processed(msg_id):
            print(f"Skipping cached email ID: {msg_id}")
            continue

        body = email.get("body", "")
        if not body: continue

        print(f"🧠 Analyzing Email {index} (ID: {msg_id})...")
        
        # Mark as processed immediately to prevent retry loops
        mark_as_processed(msg_id)

        # LLM Analysis
        parsed = process_email_with_llm(body)
        
        if not parsed: 
            print(" -> Not important.")
            continue 

        # Notify User
        send_whatsapp_message(
            title=parsed.get("title", "No Title"),
            deadline=parsed.get("deadline", "N/A"),
            action=parsed.get("action", "N/A"),
            summary=parsed.get("summary", "N/A"),
            index=index
        )

        # Store in Context (using index 1-3 for simplicity in chat)
        # We overwrite old slots "1", "2", "3" to keep the chat menu simple
        context[sender_number][str(index)] = {
            "summary": parsed.get("summary", ""),
            "title": parsed.get("title", ""),
            "deadline": parsed.get("deadline", ""),
            "action": parsed.get("action", ""),
            "original_body": body,
            "id": msg_id,
            "threadId": email.get("threadId"),
            "internet_message_id": email.get("internet_message_id"),
            "from": email.get("from"),
            "subject": email.get("subject"),
            "reminder_sent": False
        }
        
        processed_count += 1
        time.sleep(1.0) # Rate limit

    if processed_count > 0:
        save_context(context)
        print(f"✅ Processed {processed_count} new important emails.")
    else:
        print("Unknown or no new important emails.")
