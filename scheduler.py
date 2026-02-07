import time
import schedule
import threading
from datetime import datetime, timedelta
from dateutil import parser
from context_store import load_context, save_context
from whatsapp_bot import send_whatsapp_message
from email_service import process_new_emails # Import the new polling function

def check_deadlines():
    print("⏰ Checking deadlines...")
    context = load_context()
    
    now = datetime.now()
    notification_window_hours = 24 # Notify 24 hours before
    
    updated = False
    
    if not context: return

    for user_phone, user_data in context.items():
        if not isinstance(user_data, dict): continue
        
        for email_idx, email_data in user_data.items():
            if email_idx in ['current_active_index', 'pending_draft']: continue
            if not isinstance(email_data, dict): continue

            deadline_str = email_data.get('deadline')
            reminder_sent = email_data.get('reminder_sent')
            
            # Skip if no deadline or already notified
            if not deadline_str or reminder_sent:
                continue
            
            try:
                # Parse ISO format
                deadline_dt = parser.parse(deadline_str)
                
                # Check if we are within the window (e.g. 24 hours before)
                time_diff = deadline_dt - now
                
                # Logic: Notify if within 24 hours AND in the future
                if timedelta(hours=0) < time_diff <= timedelta(hours=notification_window_hours):
                    print(f"⚠️ Sending Reminder for Email {email_idx}")
                    
                    message = (
                        f"⏰ *Deadline Reminder*\n"
                        f"📌 *Title:* {email_data.get('title')}\n"
                        f"⏳ *Due:* {deadline_str}\n"
                        f"⚠️ Less than 24 hours remaining!\n"
                        f"Reply *{email_idx}* to take action."
                    )
                    
                    # send_whatsapp_message wraps send_raw_message
                    from whatsapp_bot import send_raw_message
                    send_raw_message(message, user_phone)
                    
                    email_data['reminder_sent'] = True # Mark as sent
                    updated = True
                    
            except Exception as e:
                print(f"Error parsing date for {email_idx}: {e}")
                
    if updated:
        save_context(context)

def start_scheduler():
    # 1. Schedule Deadline Checks (e.g. every hour)
    schedule.every(1).hours.do(check_deadlines)
    
    # 2. Schedule Email Polling (e.g. every 5 minutes)
    schedule.every(5).minutes.do(process_new_emails)
    
    print("✅ Scheduler Jobs Registered:")
    print("   - Deadline Check (1h)")
    print("   - Email Poll (5m)")
    
    # Run immediately for testing startup
    # threading.Thread(target=process_new_emails).start()
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    start_scheduler()
