import random

import torch

import torch.nn as nn

import torch.nn.functional as F

import numpy as np

import json

import torch.serialization

from sklearn.feature_extraction.text import TfidfVectorizer

from sklearn.utils.class_weight import compute_class_weight



from sklearn.model_selection import train_test_split

class EmailReply(nn.Module):
    def __init__(self, input_dims, output_dims):
        super(EmailReply, self).__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_dims, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, output_dims)
        )



    def forward(self, input):

        return self.layers(input)

# Global variables for loaded model and vectorizer
vectorizer = None
model = None

def load_model_and_vectorizer():
    global vectorizer, model
    if vectorizer is None:
        try:
            # Allow sklearn TfidfVectorizer as safe global for loading
            torch.serialization.add_safe_globals([TfidfVectorizer])
            vectorizer = torch.load('vectorizer.pth', weights_only=False)
            input_dims = 5000  # Assuming max_features=5000
            output_dims = 2
            model = EmailReply(input_dims, output_dims)
            model.load_state_dict(torch.load('email_reply_model.pth', weights_only=True))
            model.eval()
        except FileNotFoundError:
            print("Model or vectorizer file not found. Please train the model first.")

def predict_reply(email_body):
    """Predict if an email should be replied to."""
    if model is None:
        load_model_and_vectorizer()
    if model is None:
        raise Exception("Model not loaded")
    model.eval()
    X_new = vectorizer.transform([email_body]).toarray()
    X_tensor = torch.tensor(X_new, dtype=torch.float32)
    with torch.no_grad():
        output = model(X_tensor)
        _, predicted = torch.max(output, 1)
        return predicted.item() == 1  # True if replied

if __name__ == '__main__':
    # Training code only runs when script is executed directly
    with open("emails.json", 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    # Extract bodies and labels
    bodies = [email['body'] for email in dataset]
    labels = [1 if email['replied'] else 0 for email in dataset]

    print(labels.count(1))
    print(labels.count(0))
    print(len(labels))

    # Vectorize text
    vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
    X = vectorizer.fit_transform(bodies).toarray()
    y = np.array(labels)

    print(X.shape)

    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    # Convert to tensors
    x_train = torch.tensor(x_train, dtype=torch.float32)
    y_train = torch.tensor(y_train, dtype=torch.long)
    x_test = torch.tensor(x_test, dtype=torch.float32)
    y_test = torch.tensor(y_test, dtype=torch.long)

    input_dims = X.shape[1]
    output_dims = 2  # replied or not

    model = EmailReply(input_dims, output_dims)

    optimizer = torch.optim.Adam(model.parameters(), lr=0.0001)
    class_weights = compute_class_weight(
        class_weight='balanced',
        classes=np.unique(y),
        y=y
    )
    weights_tensor = torch.tensor(class_weights, dtype=torch.float32)
    criterion = nn.CrossEntropyLoss(weight=weights_tensor)

    num_epochs = 10
    batch_size = 64

    for ep in range(num_epochs):
        # Shuffle data
        indices = torch.randperm(len(x_train))
        x_train_shuffled = x_train[indices]
        y_train_shuffled = y_train[indices]

        epoch_loss = 0
        num_batches = len(x_train) // batch_size

        for i in range(num_batches):
            start_idx = i * batch_size
            end_idx = start_idx + batch_size
            x_batch = x_train_shuffled[start_idx:end_idx]
            y_batch = y_train_shuffled[start_idx:end_idx]

            outputs = model(x_batch)
            loss = criterion(outputs, y_batch)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        avg_loss = epoch_loss / num_batches
        print(f"Epoch {ep+1}: loss {avg_loss:.4f}")

    model.eval()
    with torch.no_grad():
        outputs = model(x_test)
        _, predicted = torch.max(outputs, 1)
        accuracy = (predicted == y_test).sum().item() / len(y_test)
        print(f"Test Accuracy: {accuracy:.4f}")

    torch.save(model.state_dict(), 'email_reply_model.pth')
    torch.save(vectorizer, 'vectorizer.pth')

    test_body = '''
        We would like to schedule a call with you.
    '''
    print(predict_reply(test_body))
