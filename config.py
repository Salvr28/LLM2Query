import json
import os
import torch
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import google.generativeai as genai

MAX_RETRIES = 1

# ------ Embedding Model and Devices -------
# https://huggingface.co/thenlper/gte-large
embedding_model = SentenceTransformer("thenlper/gte-large")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Move embedding model to the desired device
if next(embedding_model.parameters()).is_meta:
    embedding_model.to_empty(device=DEVICE)
else:
    embedding_model.to(DEVICE)

# ------ ChromaDB Config ------
CHROMA_PATH = "chroma_data/"
chroma_client = chromadb.PersistentClient(CHROMA_PATH)

# ------ Google Gemini API ------
SECRETS_FILE = "secret.json"
GOOGLE_API_KEY = None

try:
    with open(SECRETS_FILE) as f:
        secrets = json.load(f)
    GOOGLE_API_KEY = secrets.get('GOOGLE_API_KEY')

    if not GOOGLE_API_KEY:
        raise KeyError(f"Key 'GOOGLE_API_KEY not found in {SECRETS_FILE}")
    genai.configure(api_key=GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.0-flash')

except FileNotFoundError:
    print(f"[GOOGLE API Error]: File {SECRETS_FILE} not found")
except json.JSONDecodeError:
    print(f"[GOOGLE API Error]: Wrong JSON format in {SECRETS_FILE}")
except KeyError as e:
    print(f"[GOOGLE API Key Error]: {e}")

# ------ MongoDB Schema ------
SCHEMA_FILE_PATH = 'mongodb_schema.txt'
DB_SCHEMA = None

try:
    with open(SCHEMA_FILE_PATH, 'r') as f:
        db_schema_str = f.read()
    DB_SCHEMA = json.loads(db_schema_str)

except FileNotFoundError:
    print(f"[MONGODB SCHEMA Error]: File {SCHEMA_FILE_PATH} not found")
except json.JSONDecodeError:
    print(f"[MONGODB SCHEMA Error]: Wrong JSON format in {SCHEMA_FILE_PATH}")

# ------ MongoDB URI ------
MONGO_DB_NAME = "CAMPANIA_SALUTE"
MONGO_URI_KEY = 'MONGO_BASE_URI'
#MONGO_URI_KEY = 'MONGO_M10_URI'
MONGO_URI = secrets.get(MONGO_URI_KEY)

if not MONGO_URI:
    print(f"[MONGO URI Error]: Key {MONGO_URI_KEY} not found in {SECRETS_FILE}")

