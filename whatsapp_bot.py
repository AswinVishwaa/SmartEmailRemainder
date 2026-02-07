from twilio.rest import Client
import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Configuration
WHATSAPP_PROVIDER = os.getenv("WHATSAPP_PROVIDER", "twilio") # "twilio" or "meta"

# Twilio Config
ACCOUNT_SID = os.getenv("ACCOUNT_SID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
FROM_WHATSAPP = os.getenv("FROM_WHATSAPP")
TO_WHATSAPP = os.getenv("TO_WHATSAPP")

# Meta Config
META_PHONE_ID = os.getenv("META_PHONE_ID")
META_TOKEN = os.getenv("META_TOKEN")

def send_whatsapp_message(title, deadline, action, summary, index):
    """
    Sends a WhatsApp message using the configured provider.
    """
    body = (
        f"📩 *Email {index}: {title}*\n"
        f"📅 *Deadline:* {deadline}\n"
        f"🎯 *Action:* {action}\n\n"
        f"💬 Reply with *{index}* to view summary\n"
        f"✍️ Reply with *{index}R* to generate a reply"
    )
    send_raw_message(body, TO_WHATSAPP)

def send_raw_message(body, to_number):
    """
     unified sender function
    """
    try:
        if WHATSAPP_PROVIDER == "meta":
            send_via_meta(body, to_number)
        else:
            send_via_twilio(body, to_number)
    except Exception as e:
        print(f"❌ Error sending message: {e}")

def send_via_twilio(body, to_number):
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    # Twilio expects "whatsapp:+12345"
    if not to_number.startswith("whatsapp:"):
        to_number = f"whatsapp:{to_number}"
        
    msg = client.messages.create(
        body=body,
        from_=FROM_WHATSAPP,
        to=to_number
    )
    print(f"✅ Twilio Message sent! SID: {msg.sid}")

def send_via_meta(body, to_number):
    """
    Sends using WhatsApp Cloud API (Graph API)
    """
    url = f"https://graph.facebook.com/v19.0/{META_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {META_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Clean number (remove "whatsapp:" prefix if present)
    clean_number = to_number.replace("whatsapp:", "").replace("+", "")
    
    payload = {
        "messaging_product": "whatsapp",
        "to": clean_number,
        "type": "text",
        "text": {"body": body}
    }
    
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 200:
        print(f"✅ Meta Message sent!")
    else:
        print(f"❌ Meta Error: {res.text}")
