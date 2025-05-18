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
query_generator = MongoDBQueryGenerator(config.embedding_model, config.gemini_model, config.chroma_client, config.DB_SCHEMA)


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
            generated_query, context = query_generator.generate_query(prompt)

        # Rimuovi i delimitatori Markdown se presenti
        if generated_query.startswith("```mongodb"):
            generated_query = generated_query[len("```mongodb"):].strip()
        if generated_query.endswith("```"):
            generated_query = generated_query[:-len("```")].strip()

        # Esegui la query MongoDB e mostra i risultati
        query_error = False  # Inizializza una variabile per tracciare gli errori
        with st.spinner("Eseguo la query su MongoDB..."):
            try:
                query_result = execute_mongodb_query(generated_query, config.MONGO_URI, config.MONGO_DB_NAME)
                st.markdown("**📦 Risultato della Query:**")
                st.json(query_result)
            except Exception as e:
                st.error(f"Errore durante l'esecuzione della query: {e}")
                query_error = True  # Imposta la variabile di errore a True
                st.session_state.last_error = str(e) # Salva l'errore nello stato

        # Mostra la query generata solo su richiesta
        with st.expander("🧾 **Mostra Query Generata**"):
            st.markdown(f"```javascript\n{generated_query}\n```")

        # Mostra il contesto RAG
        with st.expander("📚 **Mostra Contesto RAG**"):
            st.markdown(f"```\n{context}\n```")

        # Bottone per la modifica manuale della query in caso di errore
        if query_error:
            if st.button("✏️ Modifica ed Esegui la Query Manualmente", key="edit_query_button"):
                st.session_state.manual_query_mode = True
                st.session_state.manual_query = generated_query
            else:
                st.session_state.manual_query_mode = False
                if "manual_query" in st.session_state:
                    del st.session_state.manual_query

        # Mostra l'input per la query manuale e il bottone di esecuzione
        if "manual_query_mode" in st.session_state and st.session_state.manual_query_mode:
            manual_query = st.text_area("Modifica la query MongoDB:", st.session_state.get("manual_query", ""), height=200)
            if st.button("🚀 Esegui Query Modificata", key="execute_manual_query"):
                with st.spinner("Eseguo la query modificata..."):
                    try:
                        manual_query_result = execute_mongodb_query(manual_query, config.MONGO_URI, config.MONGO_DB_NAME)
                        st.markdown("**📦 Risultato della Query Modificata:**")
                        st.json(manual_query_result)
                        if "last_error" in st.session_state:
                            del st.session_state.last_error # Cancella l'errore precedente
                        st.session_state.manual_query_mode = False # Disabilita la modalità manuale dopo l'esecuzione
                        if "manual_query" in st.session_state:
                            del st.session_state.manual_query # Cancella la query manuale
                    except Exception as e:
                        st.error(f"Errore durante l'esecuzione della query modificata: {e}")
                        st.session_state.last_error = str(e) # Aggiorna l'errore

        # Appendi il messaggio dell'assistente (senza i dettagli degli expander)
        assistant_content = "Ho provato a generare ed eseguire una query per te."
        if query_error and "last_error" in st.session_state:
            assistant_content += f"\n\nSi è verificato un errore: `{st.session_state.last_error}`. Puoi provare a modificarla manualmente."
        elif not query_error:
            assistant_content += "\n\nEcco i risultati (vedi sopra)."
        st.session_state.messages.append({"role": "assistant", "content": assistant_content})
