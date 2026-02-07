from webhook_handler import app
from models import init_db
from scheduler import start_scheduler
import threading
import time

def start_background_services():
    # 1. Init DB
    init_db()
    
    # 2. Start Scheduler
    # We run this in a daemon thread so it dies when the main app dies
    t = threading.Thread(target=start_scheduler, daemon=True)
    t.start()
    print("⏰ Scheduler running in background.")

if __name__ == "__main__":
    print("🚀 Starting Background Services...")
    start_background_services()
    print("🚀 Starting Webhook Server...")
    app.run(port=5000, debug=True, use_reloader=False) 
    # use_reloader=False prevents double initialization of threads in debug mode
