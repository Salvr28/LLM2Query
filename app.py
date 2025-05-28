import streamlit as st

st.set_page_config(layout="wide")

import json
import pandas as pd
from datetime import datetime
from query_generator import MongoDBQueryGenerator
from query_executor import execute_mongodb_query
import config
import analytics_dashboard as ad
from pymongo import MongoClient
import matplotlib.pyplot as plt

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

# ----------------------------- Streamlit Interface ----------------------------------------------------
st.title("QueryDoctor")

# --- Session State for correctness ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "df_to_display" not in st.session_state:
    st.session_state.df_to_display = None
if "context_to_display" not in st.session_state:
    st.session_state.context_to_display = None
if "show_last_query_results" not in st.session_state:
    st.session_state.show_last_query_results = False

# --- Menu Laterale ---
st.sidebar.title("Menu Navigazione")
app_mode = st.sidebar.selectbox(
    "Seleziona la modalità",
    ["Assistente", "Analitiche", "Cartella Clinica Paziente"]
)

if app_mode == "Assistente":
    st.sidebar.info("Chiedi qualsiasi cosa riguardo il tuo database. L'assistente cercherà di interpretare i tuoi bisogni e di fornirti un risultato adeguato.")
    st.header("Assistente")

    # Visualize all messages in session state
    for msg_idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)

    if prompt := st.chat_input("Chiedimi qualcosa..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Reset dello stato per i nuovi risultati che verranno visualizzati dalla sezione persistente
        st.session_state.df_to_display = None
        st.session_state.context_to_display = None
        st.session_state.show_last_query_results = False

        parts_for_history_and_immediate_display = []

        with st.spinner("Sto generando la query..."):
            generated_query, error_message, context = query_generator.generate_query(prompt)

        if context:
            st.session_state.context_to_display = context # Salva per la sezione persistente

        if error_message:
            error_display_text = f"Si è verificato un errore persistente nella generazione della query:\n```text\n{error_message}\n```"
            parts_for_history_and_immediate_display.append(error_display_text)
        elif generated_query:
            query_json_for_history = f"**Query JSON generata con successo:**\n```json\n{generated_query}\n```"
            parts_for_history_and_immediate_display.append(query_json_for_history)
            try:
                query_dict = json.loads(generated_query)
                if query_dict.get("error_type") == "irrelevant_request":
                    msg_irrelevant = query_dict.get("message", "Richiesta non pertinente.")
                    parts_for_history_and_immediate_display.append(f"\n**Nota:** {msg_irrelevant}")
                else:
                    if db is not None:
                        with st.spinner("Esecuzione della query..."):
                            query_result = execute_mongodb_query(db, query_dict)

                        if query_result['success']:
                            if query_result['data']:
                                try:
                                    df_full = pd.DataFrame(query_result['data'])
                                    st.session_state.df_to_display = df_full # Salva per la sezione persistente
                                    st.session_state.show_last_query_results = True

                                    display_limit = 20
                                    displayed_rows = min(display_limit, len(df_full))

                                except Exception as e_df:
                                    err_format_msg = f"\n**Errore formattazione tabella:** {e_df}\n**Risultati (JSON):**\n```json\n{json.dumps(query_result['data'], indent=2, ensure_ascii=False)}\n```"
                                    parts_for_history_and_immediate_display.append(err_format_msg)
                            else: # No data
                                parts_for_history_and_immediate_display.append("\nNessun risultato trovato.")
                        else: # Query execution failed
                            parts_for_history_and_immediate_display.append(f"\n**Errore Esecuzione:**\n{query_result['error']}")
                    else: # DB instance is None
                        parts_for_history_and_immediate_display.append("\n**Errore Esecuzione:** Connessione al database non disponibile.")
            except json.JSONDecodeError as e:
                parts_for_history_and_immediate_display.append(f"\n**Errore Parsing JSON (LLM Output):** {e}\nLLM Output:\n{generated_query}")
            except Exception as e:
                parts_for_history_and_immediate_display.append(f"\n**Errore Imprevisto:** {e}")

        # Mostra il messaggio dell'assistente nella chat e salvalo nella history
        if parts_for_history_and_immediate_display:
            assistant_response_content = "\n".join(parts_for_history_and_immediate_display)
            with st.chat_message("assistant"):
                st.markdown(assistant_response_content, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": assistant_response_content})

        # Se abbiamo risultati o contesto da mostrare nella sezione persistente, forziamo un rerun
        # per farla apparire subito sotto la chat.
        if st.session_state.show_last_query_results or st.session_state.context_to_display:
            st.rerun()

    # ---- SEZIONE DI VISUALIZZAZIONE PERSISTENTE ----
    # Questa sezione viene eseguita SEMPRE DOPO il blocco 'if prompt' (se c'è stato input)
    # e dopo il loop dei messaggi, quindi ad ogni rerun.

    if st.session_state.get('df_to_display') is not None:
        st.sidebar.write(f"DF empty: {st.session_state.df_to_display.empty}")

    if st.session_state.show_last_query_results and st.session_state.df_to_display is not None:
        st.markdown("---") # Separatore visivo

        df_display = st.session_state.df_to_display
        if not df_display.empty:
            display_limit = 20
            displayed_rows = min(display_limit, len(df_display))

            st.write(f"Visualizzazione delle prime {displayed_rows} righe su {len(df_display)} totali:")
            st.dataframe(df_display.head(display_limit))

            csv_data = df_display.to_csv(index=False).encode('utf-8')
            unique_download_key = f"download_csv_{len(df_display)}_{df_display.columns.tolist()}"

            st.download_button(
                label="📥 Scarica risultati completi (CSV)",
                data=csv_data,
                file_name=f"risultati_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key=unique_download_key
            )
        else:
            st.info("L'ultima query è stata eseguita con successo ma non ha prodotto dati.")

    if st.session_state.context_to_display:
        with st.expander("Contesto RAG Utilizzato (dall'ultima query)", expanded=False):
            st.markdown(st.session_state.context_to_display)

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
            "Distribuzione Pazienti per Comune di nascita",
            "Principali Motivi di decesso",
            "Numero Pazienti per Evento"
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

        elif chosen_analytics == "Distribuzione Pazienti per Comune di nascita":
            data_df, error = ad.get_distribuzione_comune_di_nascita(db)
            if error: 
                st.error(error)
            elif not data_df.empty:
                st.subheader("Distribuzione Pazienti per Comune di nascita")
                st.dataframe(data_df)
                if "Comune di nascita" in data_df.columns and "Numero Pazienti" in data_df.columns:
                    st.bar_chart(data_df.set_index("Comune di nascita"))
            else:
                st.info("Nessun dato disponibile per questa analisi") 

        elif chosen_analytics == "Distribuzione Età":
            pass

        elif chosen_analytics == "Principali Motivi di decesso":
            data_df, error = ad.get_principali_cause_decesso(db)
            if error:
                st.error(error)
            elif not data_df.empty:
                st.subheader("Principali Motivi di decesso")
                st.dataframe(data_df)
                if "Motivo del decesso" in data_df.columns and "Numero Pazienti deceduti" in data_df.columns:

                    fig, ax = plt.subplots(figsize=(10,6))
                    ax.barh(data_df["Motivo del decesso"], data_df["Numero Pazienti deceduti"], color="skyblue")
                    ax.invert_yaxis()

                    ax.set_xlabel("Numero Pazienti deceduti")
                    ax.set_ylabel("Motivo del decesso")
                    ax.set_title("Principali Motivi di decesso")

                    plt.tight_layout()
                    st.pyplot(fig)

            else:
                st.info("Nessun dato disponibile per questa analisi")

        elif chosen_analytics == "Numero Pazienti per Evento":
            data_df, error = ad.get_pazienti_per_evento(db)
            if error:
                st.error(error)
            elif not data_df.empty:
                st.subheader("Numero Pazienti per evento")
                st.dataframe(data_df)
                if "Tipo evento" in data_df.columns and "Numero Pazienti" in data_df.columns:

                    fig, ax = plt.subplots(figsize=(10,6))
                    ax.barh(data_df["Tipo evento"], data_df["Numero Pazienti"], color="green")
                    ax.invert_yaxis()

                    ax.set_xlabel("Numero Pazienti")
                    ax.set_ylabel("Tipo evento")
                    ax.set_title("Numero pazienti per evento")

                    plt.tight_layout()
                    st.pyplot(fig)

            else:
                st.info("Nessun dato disponibile per questa analisi")
        

elif app_mode == "Cartella Clinica Paziente":
    st.sidebar.info("Qui puoi cercare un paziente per codice fiscale o codice paziente e sezione. Potrai ottenere la cartella clinica digitale del paziente.")
    st.header("Cartella Clinica Paziente")

    if db is None:
        st.error(f"Impossibile connettersi al database. Controlla la configurazione.")
    else:

        type_of_search = st.radio("Scegli la modalità di ricerca:",                       
            ("Codice Fiscale", "Codice Paziente + Sezione")
        )

        research_data = {}
        exec_research = False
        if type_of_search == "Codice Fiscale":

            fiscal_code = st.text_input("Inserisci il codice fiscale del paziente.")
            if st.button("Cerca il Paziente"):
                if fiscal_code:
                    research_data = {"type": "fiscal_code", "value": fiscal_code}
                    exec_research = True
                else: 
                    st.warning("Per favore, inserisci il codice fiscale.")

        elif type_of_search == "Codice Paziente + Sezione":

            col1, col2 = st.columns(2)
            with col1:
                patient_code = st.text_input("Inserisci il codice del paziente.")
            with col2:
                patient_section = st.text_input("Inserisci la sezione del paziente.")

            if st.button("Cerca Paziente"):
                if patient_code and patient_section:
                    research_data = {
                        "type": "code_section",
                        "code": patient_code,
                        "section": patient_section    
                    }
                    exec_research = True
                else:
                    st.warning("Per favore, inserire codice paziente e sezione.")
            
        if exec_research:
            st.success(f"Dati per la ricerca: {research_data}")
            data_df, error = ad.get_lista_eventi(db, research_data)
            if error: 
                st.error(error)
            elif not data_df.empty:
                st.subheader("Lista eventi del paziente")
                st.dataframe(data_df)
            else:
                st.info("Nessun dato disponibile per questa analisi")

        
