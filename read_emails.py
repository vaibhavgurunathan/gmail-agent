import os
import base64
import json
import threading
from google.cloud import pubsub_v1
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Configuration
PROJECT_ID = "your-project-id"  # Replace with your Google Cloud Project ID - Hidden for safety
TOPIC_NAME = f"projects/{PROJECT_ID}/topics/gmail-notifications"
SUBSCRIPTION_NAME = f"projects/{PROJECT_ID}/subscriptions/gmail-notifications-sub"
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/pubsub'
]

class EmailListener:
    def __init__(self, custom_callback=None):
        self.service, self.creds = self.get_gmail_service()
        self.subscriber = pubsub_v1.SubscriberClient(credentials=self.creds)
        self.processed_message_ids = set()  # Track processed message IDs to prevent rereading
        self.service_lock = threading.Lock()  # Lock to prevent simultaneous API calls
        self.custom_callback = custom_callback

    def get_gmail_service(self):
        """Handles OAuth2 authentication and returns service and credentials."""
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        return build('gmail', 'v1', credentials=creds), creds

    def get_email_details(self, message_id):
        """Fetches the sender, subject, and body of a specific message ID."""
        msg = self.service.users().messages().get(userId='me', id=message_id, format='full').execute()
        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
        sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
        body = self.extract_body(msg['payload'])
        return sender, subject, body

    def extract_body(self, payload):
        """Extracts the plain text body from the message payload."""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    return base64.urlsafe_b64decode(data).decode('utf-8') if data else ''
        else:
            data = payload['body'].get('data', '')
            return base64.urlsafe_b64decode(data).decode('utf-8') if data else ''
        return ''

    def callback(self, message):
        """Handles incoming Pub/Sub messages."""
        with self.service_lock:
            try:
                data = json.loads(message.data.decode('utf-8'))
                print(f"\n[!] Notification for: {data.get('emailAddress')}")

                # Fetch latest email
                results = self.service.users().messages().list(userId='me', maxResults=1).execute()
                messages = results.get('messages', [])

                if messages:
                    message_id = messages[0]['id']
                    if message_id in self.processed_message_ids:
                        print(f"    Email {message_id} already processed. Skipping.")
                    else:
                        sender, subject, body = self.get_email_details(message_id)
                        print(f"    FROM: {sender}")
                        print(f"    SUBJECT: {subject}")
                        if self.custom_callback:
                            self.custom_callback(sender, subject, body)
                        self.processed_message_ids.add(message_id)
            
            except Exception as e:
                print(f"    Processing error: {e}")
            
            message.ack()

    def listen(self):
        """Starts listening for email notifications."""
        self.service.users().watch(userId='me', body={'topicName': TOPIC_NAME, 'labelIds': ['INBOX']}).execute()
        print(f"[*] Watch active. Listening for pings on {SUBSCRIPTION_NAME}...")

        flow_control = pubsub_v1.types.FlowControl(max_messages=1)
        streaming_pull_future = self.subscriber.subscribe(
            SUBSCRIPTION_NAME, 
            callback=self.callback, 
            flow_control=flow_control
        )

        with self.subscriber:
            try:
                streaming_pull_future.result()
            except KeyboardInterrupt:
                streaming_pull_future.cancel()

if __name__ == "__main__":
    listener = EmailListener()
    listener.listen()
