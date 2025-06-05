import streamlit as st
import json
import pandas as pd
import logging
from datetime import datetime
from src.query_engine.query_generator import MongoDBQueryGenerator
from src.query_engine.query_executor import execute_mongodb_query
import config
import src.app.analytics_dashboard as ad
from pymongo import MongoClient
import matplotlib.pyplot as plt
import squarify
import re
import os

# ---- Logger Configuration ----
logger = logging.getLogger('QueryDelCuoreApp')
logger.setLevel(logging.DEBUG)

log_dir = "logs"
log_file_path = os.path.join(log_dir, "app_activity.log")
os.makedirs(log_dir, exist_ok=True)

fh = logging.FileHandler(log_file_path, encoding='utf-8')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(fh)

# ---- Streamlit Page Configuration ----
st.set_page_config(
    layout="wide",
    page_title="QueryDelCuore",
    page_icon="assets/query_cuore_logo.png",
    initial_sidebar_state="expanded"
)

# ------ Critic Configuration ------
if config.GOOGLE_API_KEY is None:
    st.error('GOOGLE API Key not configured correctly in config module')
    logger.critical('GOOGLE API Key not configured')
    st.stop()
if config.DB_SCHEMA is None:
    st.error('MongoDB Schema not loaded correctly from config module')
    logger.critical('MongoDB Schema not loaded')
    st.stop()
if config.MONGO_URI is None:
    st.error('MongoDB URI not configured correctly in config module')
    logger.critical('MongoDB URI not configured')
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
        logger.error(f"Errore di connessione al database: {e}", exc_info=True)
        return None

db = init_db_connection()

#  Function to extract document names from RAG context
def extract_doc_names_from_rag_context(rag_context):
    if not rag_context:
        return []
    doc_names = []
    try:
        if isinstance(rag_context, str):
            logger.debug("DEBUG: rag_context_data È una stringa. Tentativo di parsing di tutti i nomi.")

            # Trova tutte le corrispondenze del pattern nella stringa concatenata
            # Pattern: cerca "# Tabella: NOME", "## Collezione: NOME", o "## Documento: NOME" all'inizio di una riga
            # [\w\s.-]+ cattura il nome (caratteri alfanumerici, spazi, punti, trattini)
            matches = re.findall(r"^(?:# Tabella:|## Collezione:|## Documento:)\s*([\w\s.-]+)", rag_context, re.IGNORECASE | re.MULTILINE)

            if matches:
                for extracted_name in matches:
                    doc_names.append(extracted_name.strip())
                logger.info(f"Nomi documenti/tabelle estratti dal contesto RAG (stringa): {', '.join(doc_names)}")
            else:
                logger.warning("Contesto RAG è una stringa, ma pattern nomi non trovato. Uso un placeholder.")
                doc_names.append(f"Contesto Testuale (Inizio: '{rag_context[:50].strip().replace(chr(10), ' ')}...')")
            return doc_names
    except Exception as e:
        return ["Errore estrazione nomi documenti"]

# ----------------------------- Streamlit Interface ----------------------------------------------------
st.title("LLM2Query")

# --- Session State for correctness ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "df_to_display" not in st.session_state:
    st.session_state.df_to_display = None
#if "context_to_display" not in st.session_state:
#    st.session_state.context_to_display = None
if "show_last_query_results" not in st.session_state:
    st.session_state.show_last_query_results = False

# --- Side Menu ---
st.sidebar.image("assets/query_cuore_logo.jpg", width=250)
st.sidebar.title("Menu Navigazione")
app_mode = st.sidebar.selectbox(
    "Seleziona la modalità",
    ["Assistente", "Analitiche", "Cartella Clinica Paziente"]
)

# --- Assistant mode ---
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
        logger.info(f"Nuovo prompt dall'utente: {prompt}")

        # Reset status for new results to be displayed by the persistent section
        st.session_state.df_to_display = None
        st.session_state.show_last_query_results = False

        parts_for_history_and_immediate_display = []

        with st.spinner("Sto generando la query..."):
            generated_query, error_message, context = query_generator.generate_query(prompt)

        if context:
            doc_names = extract_doc_names_from_rag_context(context)
            logger.info(f"Documenti utilizzati dal contesto RAG: {', '.join(doc_names)}")

        if error_message:
            error_display_text = f"Si è verificato un errore persistente nella generazione della query:\n```text\n{error_message}\n```"
            parts_for_history_and_immediate_display.append(error_display_text)
            logger.error(f"Errore generazione query: {error_message}")
        elif generated_query:
            logger.info(f"Query JSON generata: {generated_query}")
            query_json_for_history = f"**Query JSON generata con successo.** (Dettagli registrati nel file di log)."
            parts_for_history_and_immediate_display.append(query_json_for_history)
            try:
                query_dict = json.loads(generated_query)
                if query_dict.get("error_type") == "irrelevant_request":
                    msg_irrelevant = query_dict.get("message", "Richiesta non pertinente.")
                    parts_for_history_and_immediate_display.append(f"\n**Nota:** {msg_irrelevant}")
                else:
                    if db is not None:
                        with st.spinner("Esecuzione della query..."):
                            logger.info(f"Esecuzione query: {json.dumps(query_dict)}")
                            query_result = execute_mongodb_query(db, query_dict)

                        if query_result['success']:
                            logger.info("Esecuzione query riuscita.")
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
                                logger.info("Query eseguita, nessun risultato.")
                        else: # Query execution failed
                            parts_for_history_and_immediate_display.append(f"\n**Errore Esecuzione:**\n{query_result['error']}")
                    else: # DB instance is None
                        parts_for_history_and_immediate_display.append("\n**Errore Esecuzione:** Connessione al database non disponibile.")
            except json.JSONDecodeError as e:
                parts_for_history_and_immediate_display.append(f"\n**Errore Parsing JSON (LLM Output):** {e}\nLLM Output:\n{generated_query}")
            except Exception as e:
                parts_for_history_and_immediate_display.append(f"\n**Errore Imprevisto:** {e}")

        # Show the assistant's message in the chat and save it in the history
        if parts_for_history_and_immediate_display:
            assistant_response_content = "\n".join(parts_for_history_and_immediate_display)
            with st.chat_message("assistant"):
                st.markdown(assistant_response_content, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": assistant_response_content})

        # If we have results or context to show in the persistent section, we force a rerun
        # to make it appear immediately below the chat.
        if st.session_state.show_last_query_results:
            st.rerun()

    # ---- PERSISTENT DISPLAY SECTION
    # This section is ALWAYS executed AFTER the 'if prompt' block (if there was input)
    # and after the message loop, then at each rerun.

    if st.session_state.show_last_query_results and st.session_state.df_to_display is not None:
        st.markdown("---")

        df_display = st.session_state.df_to_display
        if not df_display.empty:
            display_limit = 20
            displayed_rows = min(display_limit, len(df_display))

            st.write(f"Visualizzazione delle prime {displayed_rows} righe su {len(df_display)} totali:")
            st.dataframe(df_display.head(display_limit))

            csv_data = df_display.to_csv(index=False).encode('utf-8')
            unique_download_key = f"download_csv_{datetime.now().timestamp()}"

            st.download_button(
                label="📥 Scarica risultati completi (CSV)",
                data=csv_data,
                file_name=f"risultati_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key=unique_download_key
            )
        else:
            st.info("L'ultima query è stata eseguita con successo ma non ha prodotto dati.")

# ---- Analytic Mode ----
elif app_mode == "Analitiche":
    st.sidebar.info("Visualizza le analitiche del tuo database. Le analitiche sono predefinite e non richiedono input da parte dell'utente.")
    st.header("Analitiche Cliniche")

    if db is None:
        st.error("Impossibile connettersi al database. Controlla la configurazione.")
    else:
        analytics_options = [
            "--- Seleziona un'analitica ---",
            "Distribuzione Pazienti per Sesso",
            "Casi di Scompensi cardiaci per anno",
            "Distribuzione Pazienti per Comune di nascita",
            "Principali Motivi di decesso",
            "Numero Pazienti per Evento",
            "Lesioni coronografiche"
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

        elif chosen_analytics == "Casi di Scompensi cardiaci per anno":
            data_df, error = ad.get_heart_failure_by_year(db)
            if error:
                st.error(error)
            elif not data_df.empty:
                st.subheader("Numero di Casi di Heart Failure per Anno")
                st.dataframe(data_df)

                if "Anno" in data_df.columns and "Numero Casi" in data_df.columns:
                    fig, ax = plt.subplots(figsize=(12,6))
                    ax.plot(data_df["Anno"], data_df["Numero Casi"], marker='o', linestyle='-', color='purple')

                    ax.set_xlabel("Anno", fontsize=12)
                    ax.set_ylabel("Numero Casi", fontsize=12)
                    ax.set_title("Andamente Annuale dei Casi di Scompenso cardiaco", fontsize=14)
                    ax.grid(True, linestyle='--', alpha=0.7)

                    ax.set_xticks(data_df["Anno"].astype(int))
                    ax.tick_params(axis='x', rotation=45)

                    plt.tight_layout()
                    st.pyplot(fig)
                else:
                    st.warning("Le colonne 'Anno' o 'Numero Casi' non sono state trovate nei dati. Verifica la query MongoDB e le intestazioni.")
            else:
                st.info("Nessun dato disponibile per l'analisi dei casi di Heart Failure per anno.")


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

        elif chosen_analytics == "Lesioni coronografiche":
            csv_file_path = os.path.join("src", "evaluation", "gold_results", "results_query_n18.csv")
            logger.info(f"Tentativo caricamento CSV Lesioni da: {csv_file_path}")
            try:
                temp_df = pd.read_csv(csv_file_path)
                error = None

                # Data transformation for treemap
                if not temp_df.empty:

                    lesion_columns = ['LESIONI_TC', 'LESIONI_IVA', 'LESIONI_CX', 'LESIONI_DX']


                    if all(col in temp_df.columns for col in lesion_columns):

                        data_for_treemap = {
                            "Tipo Lesione": [],
                            "Numero Pazienti": []
                        }
                        for col in lesion_columns:
                            data_for_treemap["Tipo Lesione"].append(col)
                            data_for_treemap["Numero Pazienti"].append(temp_df[col].iloc[0])

                        data_df = pd.DataFrame(data_for_treemap)
                    else:
                        st.error("Il file CSV non contiene tutte le colonne di lesione attese (LESIONI_TC, LESIONI_IVA, LESIONI_CX, LESIONI_DX).")
                        data_df = pd.DataFrame()
                else:
                    data_df = pd.DataFrame()


            except FileNotFoundError:
                data_df = pd.DataFrame()
                error = f"Il file '{csv_file_path}' non è stato trovato. Assicurati che il percorso sia corretto."
            except Exception as e:
                data_df = pd.DataFrame()
                error = f"Si è verificato un errore durante il caricamento o la trasformazione del file CSV: {e}"

            if error:
                st.error(error)
            elif not data_df.empty:
                st.subheader("Conteggio Pazienti per Tipo di Lesione (Treemap)")


                if "Tipo Lesione" in data_df.columns and "Numero Pazienti" in data_df.columns:
                    fig, ax = plt.subplots(figsize=(12, 7))


                    labels = [f"{row['Tipo Lesione']}\n({row['Numero Pazienti']})"
                                for index, row in data_df.iterrows()]

                    squarify.plot(sizes=data_df["Numero Pazienti"],
                                    label=labels,
                                    alpha=0.8,
                                    ax=ax,
                                    pad=True,
                                    text_kwargs={'fontsize': 10, 'color': 'white'})

                    ax.set_title("Numero Pazienti per Tipo di Lesione", fontsize=16)
                    plt.axis('off')
                    plt.tight_layout()
                    st.pyplot(fig)
                else:
                    st.warning("Errore interno: Le colonne 'Tipo Lesione' o 'Numero Pazienti' non sono state create correttamente.")
            else:
                st.info("Nessun dato disponibile per le lesioni.")


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
            #st.success(f"Dati per la ricerca: {research_data}")

            # Doing all queries for the clinical record
            events_list_df, error = ad.get_lista_eventi(db, research_data)

            if error:
                st.error(error)
            elif not events_list_df.empty:
                st.subheader("Lista eventi del paziente")
                st.dataframe(events_list_df)

                # Check if there is an anamnesi event to do other queries
                if events_list_df["Tipo evento"].isin(['ANAMNESI']).any():

                    # Get patient id to easier queries
                    patient_id = events_list_df["Id Paziente"].iloc[0]

                    last_anamnesi_date_df, error = ad.get_last_anamnesi_data(db, patient_id)
                    last_date = last_anamnesi_date_df["Data evento"].iloc[0]

                    values_anamnesi_df, error = ad.get_most_worth_from_anamnesi(db, patient_id, last_date)
                    st.subheader("Ultima Anamnesi del Paziente")
                    st.dataframe(values_anamnesi_df)


            else:
                st.info("Nessun dato disponibile per questa analisi")


