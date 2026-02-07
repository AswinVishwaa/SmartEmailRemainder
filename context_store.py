from models import SessionLocal, User, Email
import json
from datetime import datetime

# Compatibility Layer: mimics the old Dict structure but reads/writes to DB.
# Old Structure:
# {
#   "phone_number": {
#       "current_active_index": "1",
#       "pending_draft": "...",
#       "1": { ... email data ... },
#       "2": { ... email data ... }
#   }
# }

def load_context():
    session = SessionLocal()
    context = {}
    try:
        users = session.query(User).all()
        for user in users:
            user_data = {}
            if user.current_active_email_id:
                # Find the menu index for this ID
                active_email = session.query(Email).filter_by(id=user.current_active_email_id).first()
                if active_email:
                    user_data["current_active_index"] = str(active_email.menu_index)
            
            if user.pending_draft:
                user_data["pending_draft"] = user.pending_draft
            
            # Load Emails
            emails = session.query(Email).filter_by(user_phone=user.phone_number).limit(20).all()
            print(f"   -> Loaded {len(emails)} emails for {user.phone_number}")
            for email in emails:
                if email.menu_index:
                    print(f"      -> Email Index {email.menu_index} (ID: {email.id})")
                    user_data[str(email.menu_index)] = {
                        "id": email.id,
                        "threadId": email.thread_id,
                        "internet_message_id": email.internet_message_id,
                        "title": email.title,
                        "subject": email.subject,
                        "summary": email.summary,
                        "action": email.action,
                        "deadline": email.deadline.isoformat() if email.deadline else None,
                        "from": email.sender_info,
                        "original_body": email.original_body,
                        "reminder_sent": email.reminder_sent
                    }
            
            context[user.phone_number] = user_data
    except Exception as e:
        print(f"❌ DB Load Error: {e}")
    finally:
        session.close()
    return context

def check_if_processed(msg_id):
    session = SessionLocal()
    from models import ProcessedEmail
    exists = session.query(ProcessedEmail).filter_by(id=msg_id).first() is not None
    session.close()
    return exists

def mark_as_processed(msg_id):
    session = SessionLocal()
    from models import ProcessedEmail
    try:
        new_entry = ProcessedEmail(id=msg_id)
        session.add(new_entry)
        session.commit()
    except:
        session.rollback() # Ignore duplicates
    finally:
        session.close()

def save_context(context_dict):
    """
    Syncs the Dictionary back to the DB.
    """
    session = SessionLocal()
    try:
        print(f"💾 Saving Context for {len(context_dict)} users...")
        for phone, data in context_dict.items():
            if not phone: continue

            # 1. Get or Create User
            user = session.query(User).filter_by(phone_number=phone).first()
            if not user:
                print(f"   -> Creating NEW User: {phone}")
                user = User(phone_number=phone)
                session.add(user)
                session.flush() # Flush to get it ready for relationships
            
            # 2. Update User Meta
            active_idx = data.get("current_active_index")
            if active_idx and active_idx in data:
                email_id_target = data[active_idx].get("id")
                user.current_active_email_id = email_id_target
            
            user.pending_draft = data.get("pending_draft")
            
            # 3. Upsert Emails
            for key, val in data.items():
                if isinstance(val, dict) and val.get("id"):
                    email_id = val.get("id")
                    
                    email_obj = session.query(Email).filter_by(id=email_id).first()
                    if not email_obj:
                        print(f"   -> Saving NEW Email {key} (ID: {email_id})")
                        email_obj = Email(id=email_id, user_phone=phone)
                        session.add(email_obj)
                    else:
                        email_obj.user_phone = phone
                    
                    # Update fields
                    try:
                        email_obj.menu_index = int(key)
                    except:
                        pass # Ignore Non-Integer keys like 'current_active_index'

                    email_obj.thread_id = val.get("threadId")
                    email_obj.internet_message_id = val.get("internet_message_id")
                    email_obj.title = val.get("title", "")
                    email_obj.subject = val.get("subject", "")
                    email_obj.sender_info = val.get("from")
                    email_obj.summary = val.get("summary", "")
                    email_obj.action = val.get("action", "")
                    email_obj.original_body = val.get("original_body", "")
                    email_obj.reminder_sent = val.get("reminder_sent", False)
                    
                    # Handle Deadline Parsing
                    d_str = val.get("deadline")
                    if d_str:
                        try:
                            # Try ISO format first
                            email_obj.deadline = datetime.fromisoformat(d_str)
                        except:
                            pass
            
        session.commit()
        print("✅ Context Saved Successfully.")
            
    except Exception as e:
        session.rollback()
        print(f"❌ DB Save Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
