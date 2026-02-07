from models import SessionLocal, ProcessedEmail, Base, engine
from sqlalchemy import text
import os

def clear_cache():
    print("🧹 Clearing Processed Email Cache...")
    
    session = SessionLocal()
    try:
        # 1. Clear Database Cache
        num_deleted = session.query(ProcessedEmail).delete()
        session.commit()
        print(f"✅ Deleted {num_deleted} records from 'processed_emails' table.")
        
        # 2. Clear File Cache (if exists - generic fallback)
        if os.path.exists("processed_ids.txt"):
            os.remove("processed_ids.txt")
            print("✅ Deleted 'processed_ids.txt' file.")
            
    except Exception as e:
        session.rollback()
        print(f"❌ Error clearing cache: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    clear_cache()
