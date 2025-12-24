import os
from email_reply_model import predict_reply
from vector_db import VectorDB
from read_emails import EmailListener
import subprocess
from google import genai
from google.genai import types

class Agent:
    def __init__(self):
        self.db = VectorDB()
        api_key = os.environ.get('GEMINI_KEY')
        if not api_key:
            raise ValueError("GEMINI_KEY environment variable not set")
        self.client = genai.Client(api_key=api_key)
        self.listener = EmailListener(custom_callback=self.process_email)
        print(f"Agent initialized with vector database containing {self.db.collection.count()} emails")

    def work(self):
        """Starts the email listener to process incoming emails."""
        self.listener.listen()

    def process_email(self, sender, subject, body):
        """Processes an incoming email: decides to act, drafts response, and displays."""
        if not self.should_act(body):
            return
        summary = self.summarize_email(body)
        draft = self.draft_emails(body)
        incoming_email = {
            'name': sender,
            'summary': summary,
            'draft': draft
        }
        self.display_draft(incoming_email)

    def should_act(self, email_body):
        """Decide if the agent should act on this email."""
        return predict_reply(email_body)

    def draft_emails(self, email_body):
        """Draft a response based on similar emails in the database."""
        similar_emails = self.db.query_documents(email_body, n_results=10)
        context = "Based on similar emails you've handled:\n"
        if similar_emails.get('metadatas'):
            for meta in similar_emails['metadatas'][0]:
                context += f"- {meta.get('title', 'Unknown')}\n"

        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=email_body,
            config=types.GenerateContentConfig(
                system_instruction=f"Given the following context: {context} (end of context). Draft an email response to this: ",
                temperature=0.7,
                max_output_tokens=500,
            ),
        )
        return response.text

    def summarize_email(self, email_body):
        """Summarize the given email."""
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=email_body,
            config=types.GenerateContentConfig(
                system_instruction="Summarize this email for me.",
                temperature=0.7,
                max_output_tokens=500,
            ),
        )
        return response.text

    def display_draft(self, incoming_email):
        """Display the drafted email response via notification."""
        name = incoming_email['name']
        summary = incoming_email['summary']
        response = incoming_email['draft']
        self.send_notification(
            title='Incoming Email',
            message=f'Incoming Email from {name}.\nSummary: {summary}\nSuggested Response: {response}',
            app_name='Email Agent'
        )

    def send_notification(self, title, message, app_name="Email Agent"):
        """Send a macOS notification."""
        script = f'display notification "{message}" with title "{title}" subtitle "{app_name}"'
        subprocess.run(["osascript", "-e", script])

if __name__ == '__main__':
    email_agent = Agent()
    email_agent.work()
