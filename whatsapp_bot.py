from twilio.rest import Client
from dotenv import load_dotenv
import os

load_dotenv()

ACCOUNT_SID = os.getenv("ACCOUNT_SID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
FROM_WHATSAPP = os.getenv("FROM_WHATSAPP")
TO_WHATSAPP = os.getenv("TO_WHATSAPP")

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_whatsapp_message(title, deadline, action, summary, index):
    """
    Sends a WhatsApp message using Twilio API with identifier index.
    """
    try:
        body = (
            f"📩 *Email {index}: {title}*\n"
            f"📅 *Deadline:* {deadline}\n"
            f"🎯 *Action:* {action}\n\n"
            f"💬 Reply with *{index}* to view summary\n"
            f"✍️ Reply with *{index}R* to generate a reply"
        )

        msg = client.messages.create(
            body=body,
            from_=FROM_WHATSAPP,
            to=TO_WHATSAPP
        )

        print(f"✅ Message sent! SID: {msg.sid}")
    except Exception as e:
        print(f"❌ Error sending message: {e}")

def send_raw_message(body, to_number):
    try:
        msg = client.messages.create(
            body=body,
            from_=FROM_WHATSAPP,
            to=f"whatsapp:{to_number}"
        )
        print(f"✅ Reply sent to {to_number}. SID: {msg.sid}")
    except Exception as e:
        print(f"❌ Error sending reply: {e}")
