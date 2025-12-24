# Email Agent

An AI-powered email assistant that automatically processes incoming emails, summarizes them, drafts intelligent responses based on past interactions, and notifies the user via macOS notifications.

## Features

- **Real-time Email Monitoring**: Listens for incoming emails using Gmail API and Pub/Sub notifications.
- **Smart Reply Decision**: Uses a machine learning model to determine if an email requires a response.
- **Email Summarization**: Automatically summarizes incoming emails using Google's Gemini AI.
- **Contextual Response Drafting**: Drafts responses based on similar past emails stored in a vector database.
- **Intelligent Notifications**: Sends macOS notifications with email summaries and suggested responses.

## Architecture

- **Vector Database**: ChromaDB for storing and querying email embeddings.
- **Machine Learning**: PyTorch model for reply prediction, Sentence Transformers for embeddings.
- **AI Integration**: Google Gemini for email summarization and response generation.
- **Email Integration**: Gmail API for email access and Pub/Sub for real-time notifications.

## Setup

### Prerequisites

- Python 3.8+
- Gmail account with API access
- Google Cloud Project with Gmail API and Pub/Sub enabled

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/vaibhavgurunathan/email_agent.git
   cd email_agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up Gmail API:
   - Create a Google Cloud Project
   - Enable Gmail API and Pub/Sub API
   - Create credentials (credentials.json) and place in project root
   - Set up Pub/Sub topic and subscription for Gmail notifications

4. Set environment variables:
   ```bash
   export GEMINI_KEY="your_gemini_api_key"
   ```

5. Train the reply prediction model (optional, if not using pre-trained):
   - Prepare training data in `dataset/` directory
   - Run the training notebook `email_reply_model.ipynb`

### Usage

1. Run the email agent:
   ```bash
   python agent.py
   ```

2. The agent will:
   - Authenticate with Gmail
   - Start listening for email notifications
   - Process incoming emails automatically
   - Send notifications with summaries and draft responses

## Files

- `agent.py`: Main agent class and workflow
- `read_emails.py`: Gmail API integration and email listening
- `vector_db.py`: Vector database operations
- `email_reply_model.py`: ML model for reply prediction
- `email_data_processing.py`: Data preprocessing utilities
- `requirements.txt`: Python dependencies

## Configuration

- Update PROJECT_ID and TOPIC_NAME in `read_emails.py` for your Google Cloud setup
- Adjust model paths and parameters as needed

## Security Notes

- Never commit `credentials.json`, `token.json`, or API keys to version control
- The `.gitignore` file excludes sensitive files and large data/model files

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

This project is licensed under the MIT License.
