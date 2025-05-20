import streamlit as st
import json
import torch
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import google.generativeai as genai
from query_generator import MongoDBQueryGenerator
from query_executor import execute_mongodb_query
import config

# ------ Critic Configuration ------
if config.GOOGLE_API_KEY is None:
    st.error('GOOGLE API Key not configured correctly in config module')
    st.stop()
if config.DB_SCHEMA is None:
    st.error('MongoDB Schema not loaded correctly from config module')
    st.stop()
if config.MONGO_URI is None:
    st.error('MongoDB URI not configured correctly in config module')
    st.stop()

# ------ Streamlit App Tools ------
# Qui ci dovrebbero andare tutti i moduli che usa app:
# - Query Generator
# - Query Validator
# - Query Executor
query_generator = MongoDBQueryGenerator(config.embedding_model, config.gemini_model, config.chroma_client, config.DB_SCHEMA, config.MAX_RETRIES)


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
            generated_query, error_message, context = query_generator.generate_query(prompt)

        if error_message:
            # Mostra l'errore in modo più evidente se è un errore di parsing finale
            error_display = f"Si è verificato un errore persistente nella generazione della query:\n```text\n{error_message}\n```"
            st.error(error_display) # Usa st.error per evidenziare
            assistant_response_content = error_display
        elif generated_query:
            success_message = "**Query JSON generata con successo:**"
            st.markdown(success_message)
            st.code(generated_query, language="json")
            assistant_response_content = f"{success_message}\n```json\n{generated_query}\n```"

        if context:
            with st.expander("Contesto RAG Utilizzato", expanded=False):
                #rag_expander_md = f"<br><details><summary>📚 <strong>Contesto RAG Utilizzato</strong> (click per espandere)</summary><pre><code>{context}</code></pre></details>"
                st.markdown(context)
                assistant_response_content += f"\n{context}"

    st.session_state.messages.append({"role": "assistant", "content": assistant_response_content})
