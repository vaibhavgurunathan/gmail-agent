import chromadb
from chromadb.utils import embedding_functions
import json
import hashlib

class VectorDB:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        try:
            self.collection = self.client.get_collection(name="emails", embedding_function=self.embedding_function)
        except:
            self.collection = self.client.create_collection(name="emails", embedding_function=self.embedding_function)

        if self.collection.count() == 0:
            self._load_emails_from_json()

    def _load_emails_from_json(self, batch_size=1000):
        """Load emails from JSON file in batches to avoid memory issues."""
        try:
            with open('emails.json', 'r', encoding='utf-8') as f:
                dataset = json.load(f)

            total_emails = len(dataset)
            print(f"Loading {total_emails} emails into vector database...")

            for i in range(0, total_emails, batch_size):
                batch = dataset[i:i + batch_size]
                ids = []
                documents = []
                metadatas = []

                for j, email in enumerate(batch):
                    unique_id = self._generate_id(email['title'], email['body'], i + j)
                    ids.append(unique_id)
                    documents.append(email['body'])
                    metadatas.append({
                        'title': email['title'],
                        'from': email['from'],
                        'to': email['to'],
                        'replied': email['replied']
                    })

                self.collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                print(f"Loaded batch {i//batch_size + 1}/{(total_emails + batch_size - 1)//batch_size}")

            print("All emails loaded successfully.")

        except FileNotFoundError:
            print("emails.json not found, starting with empty collection")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
        except Exception as e:
            print(f"Error loading emails: {e}")

    def _generate_id(self, title, body, index=None):
        # Create unique ID from title and body hash, with optional index for uniqueness
        content = f"{title}{body}"
        if index is not None:
            content += str(index)
        return hashlib.md5(content.encode()).hexdigest()

    def add_email(self, email):
        unique_id = self._generate_id(email['title'], email['body'])
        self.collection.add(
            ids=unique_id,
            documents=email['body'],
            metadatas={
                'title': email['title'],
                'from': email['from'],
                'to': email['to'],
                'replied': email['replied']
            }
        )

    def query_documents(self, query_text, n_results=10):
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results
