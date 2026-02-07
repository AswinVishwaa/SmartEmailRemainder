from flask import Flask, request
from whatsapp_bot import send_raw_message
from reply_generator import generate_reply
from context_store import load_context, save_context
from llm_processor import classify_intent, chat_with_email
from gmail_sender import send_email
import re
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route("/")
def home():
    return "Email Bot Running. Use /whatsapp for webhook.", 200

@app.route("/whatsapp", methods=["POST", "GET"])
def whatsapp_reply():
    # 0. Verification (For Meta Cloud API)
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        verify_token = os.getenv("META_VERIFY_TOKEN", "mysecrettoken")
        
        print(f"🔍 Meta Verification Attempt: Expected '{verify_token}', Received '{token}'")
        
        if mode == "subscribe" and token == verify_token:
            return challenge, 200
        return "Forbidden", 403

    # 1. Parse Payload (Unified)
    incoming_msg = ""
    sender = ""
    
    if request.is_json: # Meta Logic
        data = request.json
        try:
            entry = data['entry'][0]['changes'][0]['value']
            if 'messages' in entry:
                msg = entry['messages'][0]
                incoming_msg = msg['text']['body']
                sender = msg['from'] # Meta returns pure number e.g. "1555000"
            else:
                return "OK", 200 # Status update (read/delivered), ignore
        except:
            return "OK", 200
    else: # Twilio Logic
        incoming_msg = request.form.get("Body", "").strip()
        sender = request.form.get("From", "").replace("whatsapp:", "")

    if not incoming_msg:
        return "OK", 200

    sender = str(sender).replace("+", "") # Remove + to match Meta/DB format
    print(f"📩 Incoming message from {sender}: {incoming_msg}")

    context = load_context()
    print(f"DEBUG: Known Users in DB: {list(context.keys())}") # Debug Key Match
    user_ctx = context.get(sender, {})

    # 2. Check for Direct Email Selection (e.g., "1", "2")
    match = re.match(r"^(\d+)$", incoming_msg)
    if match:
        email_idx = match.group(1)
        if email_idx in user_ctx:
            user_ctx['current_active_index'] = email_idx
            user_ctx.pop('pending_draft', None) # Clear any old drafts
            
            email_data = user_ctx[email_idx]
            reply = (
                f"🎯 *Focused on Email {email_idx}*\n"
                f"📌 *Title:* {email_data.get('title')}\n"
                f"👤 *From:* {email_data.get('from', 'Unknown')}\n\n"
                f"🤖 *How can I help?*\n"
                "• Ask a question (e.g. \"When is the deadline?\")\n"
                "• Draft a reply (e.g. \"Accept the interview\")"
            )
        else:
            reply = f"⚠️ Email {email_idx} not found in recent context."
        
        context[sender] = user_ctx
        save_context(context)
        send_raw_message(reply, sender)
        return "OK", 200

    # 3. If no email is selected, guide the user
    if 'current_active_index' not in user_ctx:
        send_raw_message("🤖 Please reply with the email number (e.g., *1*) to start actions on it.", sender)
        return "OK", 200

    # 4. Handle Intent within Context
    email_idx = user_ctx['current_active_index']
    email_data = user_ctx.get(email_idx)
    
    if not email_data:
         send_raw_message("⚠️ Error: Active email context missing. Please select email again.", sender)
         return "OK", 200

    # Classify the user's free text
    intent = classify_intent(incoming_msg)
    print(f"🧠 Detected Intent: {intent}")

    if intent == "CANCEL":
        user_ctx.pop('pending_draft', None)
        reply = "🚫 Action cancelled. What would you like to do next?"

    elif intent == "SEND":
        if user_ctx.get('pending_draft'):
            # Extract recipient email from "First Last <email@domain.com>" format
            raw_from = email_data.get('from', '')
            recipient = raw_from
            if '<' in raw_from and '>' in raw_from:
                recipient = raw_from.split('<')[1].split('>')[0]
            
            subject = f"Re: {email_data.get('subject', 'No Subject')}"
            body = user_ctx['pending_draft']
            thread_id = email_data.get('threadId')
            msg_id = email_data.get('internet_message_id') # Standard Message-ID header
            
            # Send Email
            sent_id = send_email(to=recipient, subject=subject, body=body, thread_id=thread_id, in_reply_to=msg_id)
            
            if sent_id:
                reply = f"✅ Email sent successfully! (ID: {sent_id})"
                user_ctx.pop('pending_draft') # Clear draft
            else:
                reply = "❌ Failed to send email. Please check logs."
        else:
            reply = "⚠️ You haven't drafted a reply yet. Tell me what to say first!"

    elif intent == "DRAFT":
        # Generate a draft
        send_raw_message("✍️ Drafting your reply...", sender) # Ack
        draft = generate_reply(email_data['original_body'], instruction=incoming_msg)
        user_ctx['pending_draft'] = draft
        reply = (
            f"📝 *Draft Generated:*\n\n"
            f"{draft}\n\n"
            "-----------------------------\n"
            "Reply *Send* to confirm, or give me feedback to change it."
        )
        
    else: # QUESTION or general chat
        answer = chat_with_email(email_data['original_body'], incoming_msg)
        reply = f"🤖 {answer}"

    # Save state
    context[sender] = user_ctx
    save_context(context)
    
    send_raw_message(reply, sender)
    return "OK", 200
