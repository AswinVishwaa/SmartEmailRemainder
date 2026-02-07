from whatsapp_bot import send_whatsapp_message, send_raw_message
import time
from dotenv import load_dotenv
import os

load_dotenv()

# Ensure we use the proper key
TO_NUMBER = os.getenv("TO_WHATSAPP")
if not TO_NUMBER:
    print("❌ Error: TO_WHATSAPP is missing in .env")
    exit(1)

print(f"🚀 Sending test message to: {TO_NUMBER}")
print(f"Using Provider: {os.getenv('WHATSAPP_PROVIDER')}")

# Test 1: Raw Message
print("Sending Raw Text...")
send_raw_message("👋 Hello! This is a test from your Local Python Script.", TO_NUMBER)

# Test 2: Structured Template (Mocking an Email Alert)
print("Sending Email Alert...")
time.sleep(2)
send_whatsapp_message(
    title="Test Email: Welcome to the Bot",
    deadline="2024-12-31",
    action="Reply '1'",
    summary="This is a test notification to verify the WhatsApp API connection is working.",
    index=1
)

print("✅ Done. Check your WhatsApp!")
