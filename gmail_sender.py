import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from gmail_fetcher import authenticate_gmail

def send_email(to, subject, body, thread_id=None, in_reply_to=None):
    """
    Sends an email using the Gmail API.
    
    Args:
        to (str): Recipient email address.
        subject (str): Email subject.
        body (str): Email body text.
        thread_id (str, optional): Thread ID to reply to via Gmail threading.
        in_reply_to (str, optional): Standard Message-ID header for threading.
    """
    try:
        creds = authenticate_gmail()
        service = build('gmail', 'v1', credentials=creds)

        message = EmailMessage()
        message.set_content(body)
        message['To'] = to
        # message['From'] = 'me'  # Gmail API handles this automatically
        message['Subject'] = subject

        if in_reply_to:
            message['In-Reply-To'] = in_reply_to
            message['References'] = in_reply_to

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {
            'raw': encoded_message
        }
        
        if thread_id:
            create_message['threadId'] = thread_id

        send_message = (service.users().messages().send(userId="me", body=create_message).execute())
        
        print(f"✅ Email sent to {to}. Message Id: {send_message['id']}")
        return send_message['id']
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return None
