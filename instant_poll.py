from email_service import process_new_emails
from models import init_db

def manual_trigger():
    print("🚀 Triggering Instant Email Poll...")
    init_db() # Ensure DB is ready
    process_new_emails()
    print("✅ Instant Poll Complete.")

if __name__ == "__main__":
    manual_trigger()
