import tqdm
from sentence_transformers import SentenceTransformer
import torch

# https://huggingface.co/thenlper/gte-large
embedding_model = SentenceTransformer("thenlper/gte-large")

# Check if the model is on a meta device
if next(embedding_model.parameters()).is_meta:
    # Move to the desired device (e.g., 'cuda' for GPU, 'cpu' for CPU) using to_empty()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    embedding_model.to_empty(device=device)
else:
    # If not on a meta device, you can use .to() as usual
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    embedding_model.to(device)

import chromadb
from chromadb.config import Settings

chroma_client = chromadb.PersistentClient(path="chroma_data/")
chroma_collection = chroma_client.get_collection(name="datasets_documentations")

import google.generativeai as genai
import streamlit as st

import json

with open("secret.json") as f:
  secrets = json.load(f)

try:
    GOOGLE_API_KEY = secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
except KeyError:
    st.error("Google API Key not found in secrets.json. Please ensure it's there.")
    st.stop()

st.set_page_config(page_title="MongoDB Query Generator", page_icon="🧠")

SCHEMA_FILE_PATH = "mongodb_schema.txt"  # Assuming the file is in the same directory

try:
    with open(SCHEMA_FILE_PATH, 'r') as f:
        DB_SCHEMA_STR = f.read()
    DB_SCHEMA = json.loads(DB_SCHEMA_STR)
except FileNotFoundError:
    st.error(f"Error: Schema file not found at '{SCHEMA_FILE_PATH}'")
    st.stop()
except json.JSONDecodeError:
    st.error(f"Error: Invalid JSON format in '{SCHEMA_FILE_PATH}'")
    st.stop()


model = genai.GenerativeModel('gemini-2.0-flash') # Load the model

def retrieve_context(user_instruction: str, n_results: int = 3) -> str:
    query_embedding = embedding_model.encode(user_instruction)
    results = chroma_collection.query(query_embeddings=[query_embedding], n_results=n_results, include=["documents", "metadatas", "distances"])
    documents = results["documents"][0]
    return "\n---\n".join(documents)

def generate_query(user_instruction: str) -> str:

    context = retrieve_context(user_instruction)

    prompt = f"""<s>
    Task Description:
    Your task is to create a MongoDB query that accurately fulfills the provided Instruct while strictly adhering to the given MongoDB schema.

    MongoDB Schema:
    {DB_SCHEMA}

    Retrieved Context:
    {context}

    ### Instruct:
    {user_instruction}

    ### Output:
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip(), context
    except Exception as e:
        return f"Errore durante la generazione della query: {e}", context

# ----Streamlit Interface------
st.title("🧠 MongoDB Query Generator con Gemini Flash")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Chiedimi qualcosa..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Sto generando la query con Gemini Flash..."):
            response, context = generate_query(prompt)
        st.markdown(f"```javascript\n{response}\n```")

        with st.expander("📚 **Mostra Contesto RAG**"):
            st.markdown(f"```\n{context}\n```")

    st.session_state.messages.append({"role": "assistant", "content": f"```javascript\n{response}\n```\n\n<details><summary>📚 **Contesto RAG**</summary><pre>{context}</pre></details>"})