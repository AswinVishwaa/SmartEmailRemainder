from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Default to a local postgres DB if not specified
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/email_bot_db")

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    phone_number = Column(String, primary_key=True)
    current_active_email_id = Column(String, nullable=True) # ID of the email currently being discussed
    pending_draft = Column(Text, nullable=True) # Draft content waiting for approval
    
    emails = relationship("Email", back_populates="user")

class ProcessedEmail(Base):
    __tablename__ = 'processed_emails'
    id = Column(String, primary_key=True) # Gmail Message ID
    processed_at = Column(DateTime, default=datetime.utcnow)

class Email(Base):
    __tablename__ = 'emails'
    id = Column(String, primary_key=True) # Use Gmail Message ID
    user_phone = Column(String, ForeignKey('users.phone_number'))
    
    thread_id = Column(String)
    internet_message_id = Column(String)
    
    title = Column(String)
    subject = Column(String)
    summary = Column(Text)
    action = Column(String)
    deadline = Column(DateTime, nullable=True)
    
    sender_info = Column(String) # From field
    original_body = Column(Text)
    
    is_important = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)

    # For mapping "1", "2", "3" in the chat menu to real IDs
    # distinct per user. Ideally we'd calculate this dynamically, but storing it is easier for now.
    menu_index = Column(Integer, nullable=True) 

    user = relationship("User", back_populates="emails")

def init_db():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

# Global session factory
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
