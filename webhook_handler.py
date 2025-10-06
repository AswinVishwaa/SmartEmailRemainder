from flask import Flask, request
from whatsapp_bot import send_raw_message
from reply_generator import generate_reply
from context_store import load_context, save_context
import re

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.form.get("Body", "").strip()
    sender = request.form.get("From", "").replace("whatsapp:", "")

    print(f"📩 Incoming message from {sender}: {incoming_msg}")

    context = load_context()
    user_ctx = context.get(sender, {})

    print(f"🔍 Context for {sender}? {'Yes' if user_ctx else 'No'}")
    print(f"🧠 Full Context: {user_ctx}")

    # TONE MODE: Check if waiting for tone
    if incoming_msg.lower() in ["positive", "negative", "neutral"]:
        # Find which email is awaiting tone
        found = False
        for idx, email_data in user_ctx.items():
            if email_data.get("awaiting_tone"):
                reply_text = generate_reply(email_data.get("original_body", ""), tone=incoming_msg.lower())
                reply = f"✉️ Suggested Reply for Email {idx} ({incoming_msg.title()} Tone):\n\n{reply_text}"
                email_data["awaiting_tone"] = False
                found = True
                break
        if not found:
            reply = "⚠️ No reply request was pending. Use *1R*, *2R*, etc. first."
        else:
            context[sender] = user_ctx
            save_context(context)
            send_raw_message(reply, sender)
            return "OK", 200

    # MAIN HANDLER
    match = re.match(r"^(\d+)(R)?$", incoming_msg, re.IGNORECASE)
    if not match:
        reply = "🤖 Reply with:\n*1* to view summary\n*1R* to generate reply\n(Use 2 or 2R for second email, etc)"
    else:
        email_index = match.group(1)
        wants_reply = match.group(2) is not None

        if email_index not in user_ctx:
            reply = f"⚠️ No email with index {email_index} found."
        else:
            email_data = user_ctx[email_index]
            if wants_reply:
                email_data["awaiting_tone"] = True
                reply = (
                    f"✍️ What tone should I use to reply to Email {email_index}?\n"
                    f"Reply with: *positive*, *negative*, or *neutral*"
                )
            else:
                reply = f"📝 *Summary for Email {email_index}:*\n{email_data.get('summary', 'N/A')}"

        context[sender] = user_ctx
        save_context(context)

    send_raw_message(reply, sender)
    return "OK", 200
