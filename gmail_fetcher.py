# gmail_fetcher.py
import os.path
import base64
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email import message_from_bytes

# Updated scopes to include sending permissions
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def fetch_emails(n=3):
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)
    
    results = service.users().messages().list(userId='me', maxResults=20).execute()  # Fetch more than needed
    messages = results.get('messages', [])
    
    emails = []
    for msg in messages:
        if len(emails) >= n:
            break
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='raw').execute()
        raw_msg = base64.urlsafe_b64decode(msg_data['raw'])
        mime_msg = message_from_bytes(raw_msg)
        
        subject = mime_msg.get('Subject', '')
        from_email = mime_msg.get('From', '')
        payload = mime_msg.get_payload()
        
        # Get Message-ID and Thread-ID for threading replies
        msg_id = msg['id']
        thread_id = msg['threadId']
        # Also try to get the actual Message-ID header (useful for In-Reply-To)
        internet_message_id = mime_msg.get('Message-ID', '')

        body = ""
        if mime_msg.is_multipart():
            for part in mime_msg.walk():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
        else:
            body = payload if isinstance(payload, str) else payload.decode('utf-8', errors='ignore')
        
        if body.strip():
            emails.append({
                'id': msg_id,
                'threadId': thread_id,
                'internet_message_id': internet_message_id,
                'subject': subject,
                'from': from_email,
                'body': body
            })
    
    return emails