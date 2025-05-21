import streamlit as st

st.set_page_config(layout="wide")

import json
#import torch
#from sentence_transformers import SentenceTransformer
#import chromadb
#from chromadb.config import Settings
#import google.generativeai as genai
from query_generator import MongoDBQueryGenerator
from query_executor import execute_mongodb_query
import config
import analytics_dashboard as ad
from pymongo import MongoClient

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

@st.cache_resource
def get_query_generator():
    return MongoDBQueryGenerator(config.embedding_model, config.gemini_model, config.chroma_client, config.DB_SCHEMA, config.MAX_RETRIES)

query_generator = get_query_generator()

@st.cache_resource
def init_db_connection():
    try:
        client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        return client[config.MONGO_DB_NAME]
    except Exception as e:
        st.error(f"Errore di connessione al database: {e}")
        return None

db = init_db_connection()

# ----Streamlit Interface------
st.title("QueryDoctor")

# --- Menu Laterale ---
st.sidebar.title("Menu Navigazione")
app_mode = st.sidebar.selectbox(
    "Seleziona la modalità",
    ["Assistente", "Analitiche"]
)

if app_mode == "Assistente":
    st.sidebar.info("Chiedi qualsiasi cosa riguardo il tuo database. L'assistente cercherà di interpretare i tuoi bisogni e di fornirti un risultato adeguato.")
    st.header("Assistente")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Chiedimi qualcosa..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Sto generando la query..."):
                generated_query, error_message, context = query_generator.generate_query(prompt)

            assistant_response_parts = []


            if error_message:
                # Mostra l'errore in modo più evidente se è un errore di parsing finale
                error_display = f"Si è verificato un errore persistente nella generazione della query:\n```text\n{error_message}\n```"
                st.error(error_display) # Usa st.error per evidenziare
                assistant_response_parts.append(error_display)
            elif generated_query:
                success_message = "**Query JSON generata con successo:**"
                st.markdown(success_message)
                st.code(generated_query, language="json")
                assistant_response_parts.append(f"{success_message}\n```json\n{generated_query}\n```")

                try:

                    query_dict = json.loads(generated_query)
                    query_result = execute_mongodb_query(query_dict, config.MONGO_URI, config.MONGO_DB_NAME)

                    if query_result['success']:
                        if query_result['data']:
                            st.json(query_result['data'])
                            assistant_response_parts.append(f"{success_message}\n```json\n{generated_query}\n```\n**Risultati:**\n{json.dumps(query_result['data'], indent=2)}")
                        else:
                            st.write("Nessun risultato trovato.")
                            assistant_response_parts.append(f"{success_message}\n```json\n{generated_query}\n```\nNessun risultato trovato.")

                    else:
                        st.error(f"Errore durante l'esecuzione della query: {query_result['error']}")
                        assistant_response_parts.append(f"{success_message}\n```json\n{generated_query}\n```\n**Errore:**\n{query_result['error']}")


                except Exception as e:
                    st.error(f"Si è verificato un errore durante l'esecuzione della query: {e}")
                    assistant_response_parts.append(f"Si è verificato un errore durante l'esecuzione della query: {e}")

            if context:
                with st.expander("Contesto RAG Utilizzato", expanded=False):
                    st.markdown(context)
                    assistant_response_parts.append(f"\n\n<details><summary>📚 Contesto RAG</summary><pre><code>{context}</code></pre></details>")

        st.session_state.messages.append({"role": "assistant", "content": "\n".join(assistant_response_parts)})

elif app_mode == "Analitiche":
    st.sidebar.info("Visualizza le analitiche del tuo database. Le analitiche sono predefinite e non richiedono input da parte dell'utente.")
    st.header("Analitiche Cliniche")

    if db is None:
        st.error("Impossibile connettersi al database. Controlla la configurazione.")
    else:
        analytics_options = [
            "--- Seleziona un'analitica ---",
            "Distribuzione Pazienti per Sesso",
            "Distribuzione Età",
        ]

        chosen_analytics = st.selectbox("Seleziona un'analitica", analytics_options)

        if chosen_analytics == "Distribuzione Pazienti per Sesso":
            data_df, error = ad.get_distibuzione_sesso(db)
            if error:
                st.error(error)
            elif not data_df.empty:
                st.subheader("Distribuzione Pazienti per Sesso")
                st.dataframe(data_df)
                if 'Sesso' in data_df.columns and 'Numero Pazienti' in data_df.columns:
                    st.bar_chart(data_df.set_index('Sesso'))
            else: st.info("Nessun dato disponibile per questa analisi.")

        elif chosen_analytics == "Distribuzione Età":
            pass
