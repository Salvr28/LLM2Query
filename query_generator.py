import tqdm
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import google.generativeai as genai
import json
import re


class MongoDBQueryGenerator:
    def __init__(self, embedding_model: SentenceTransformer, model: genai.GenerativeModel, chroma_client: chromadb.PersistentClient, db_schema, max_retries: int):
        self.model = model
        self.chroma_client = chroma_client
        self.chroma_collection = self.chroma_client.get_collection(name="datasets_documentations")
        self.embedding_model = embedding_model
        self.db_schema = db_schema
        self.max_retries = max_retries

    def generate_query(self, user_instruction: str) -> tuple[str | None, str | None, str]:
        """
        Generate a MongoDB query formatted as a dictionary

        Returns:
            tuple:
                - str: LLM generated query
                - str: Error message if any
                - str: Context retrieved from the database
        """

        context = self.retrieve_context(user_instruction)

        initial_prompt = f"""<s>
        Task Description:
        Your task is to generate a **JSON object** that represents a MongoDB query to accurately fulfill the provided "Instruct", OR to indicate if the "Instruct" is irrelevant to this task.
        - If the "Instruct" is a valid request for a MongoDB query related to the provided "MongoDB Schema", generate a JSON object with "collection_name", "operation_type", and "arguments" keys as detailed below.
        - If the "Instruct" is NOT a request for a MongoDB query OR is unrelated to the provided "MongoDB Schema" (e.g., a general question like "how are you?", a request for a recipe, a math problem, etc.), you MUST output a specific JSON object in the following format:
        `{{"error_type": "irrelevant_request", "message": "Posso solo generare query MongoDB basate sullo schema e sul contesto forniti. Per favore, fai una domanda relativa all'interrogazione del database clinico."}}`
        IMPORTANT: For any filter values associated with the fields "COGNOME", "NOMEPAZ", or "COMUNE_DI_NASCITA", ensure the string value is in UPPERCASE. For example, if the user asks for "Rossi", the filter should be "COGNOME": "ROSSI".
        IMPORTANT: For any date values, ensure the format is "YYYY-MM-DDT00:00:00.000+00:00" (e.g., "2023-01-01T00:00:00.000+00:00"). This is crucial for date comparisons in MongoDB queries.

        Details for valid MongoDB query JSON:
        The JSON object MUST have the following top-level keys:
        - "collection_name": (string) The name of the MongoDB collection.
        - "operation_type": (string) The type of MongoDB operation, which MUST be either "find" or "aggregate".
        - "arguments": (object) An object containing the specific arguments for the operation.
        - For "find" operations, "arguments" MUST contain:
            - "filter": (object) The MongoDB filter document.
            - "projection": (object, optional) The MongoDB projection document.
        - For "aggregate" operations, "arguments" MUST contain:
            - "pipeline": (array) An array of MongoDB aggregation pipeline stages.

        Ensure all field names within "filter", "projection", and "pipeline" stages strictly adhere to the given MongoDB Schema.
        Output ONLY the JSON object as a valid JSON string, nothing else. DO NOT wrap it in markdown code blocks.

        MongoDB Schema:
        {self.db_schema}

        Retrieved Context (for informational purposes, use the schema for exact field names and structure):
        {context}

        Examples of desired JSON output:
        Instruct: "Mostrami tutti i pazienti nati dopo il 1940, visualizzando nome e data di nascita."
        Output:
        {{
        "collection_name": "ANAGRAFICA",
        "operation_type": "find",
        "arguments": {{
            "filter": {{"DATADINASCITA": {{"$gt": "1930-01-01T00:00:00.000+00:00"}}}},
            "projection": {{"NOMEPAZ": 1, "DATADINASCITA": 1, "_id": 0}}
        }}
        }}

        Instruct: "Quanti fumatori ci sono per ogni sezione, ordinati per sezione?"
        Output:
        {{
        "collection_name": "ANAMNESI",
        "operation_type": "aggregate",
        "arguments": {{
            "pipeline": [
                {{"$match": {{"FUMO": "YES"}}}},
                {{"$group": {{"_id": "$SEZIONE", "count": {{"$sum": 1}}}}}},
                {{"$sort": {{"SEZIONE": -1}}}}
            ]
        }}
        }}

        Instruct: "Per ogni paziente che ha il diabete, elenca il suo codice paziente e tutte le date dei suoi ricoveri ospedalieri."
        Output:
        {{
        "collection_name": "ANAMNESI",
        "operation_type": "aggregate",
        "arguments": {{
            "pipeline": [
                {{
                    "$match": {{
                        "DIABETE": "YES"
                    }}
                }},
                {{
                    "$lookup": {{
                        "from": "RICOVERO_OSPEDALIERO",
                        "localField": "ID_PAZ",
                        "foreignField": "ID_PAZ",
                        "as": "info_ricoveri"
                    }}
                }},
                {{
                    "$project": {{
                        "_id": 0,
                        "id_paziente_anamnesi": "$ID_PAZ",
                        "date_ricoveri_ospedalieri": "$info_ricoveri.DATA"
                    }}
                }}
            ]
        }}
        }}

        Instruct: "Dammi la ricetta della carbonara."
        Output:
        {{
        "error_type": "irrelevant_request",
        "message": "Posso solo generare query MongoDB basate sullo schema e sul contesto forniti. Per favore, fai una domanda relativa all'interrogazione del database clinico."
        }}

        ### Instruct (User's natural language query):
        {user_instruction}

        ### Output (JSON object as a string):
        """

        retry_prompt_template = f"""<s>
        Your previous attempt to generate a JSON object for the user's instruction resulted in an error because the output was not valid JSON.
        Please review your previous output and the error, then try again.
        **Remember, your task is to generate a MongoDB query as a JSON object according to the schema, or the specific error JSON if the request is irrelevant.**
        Ensure your output is a single, valid JSON object string, with correct syntax (quotes, commas, brackets, braces).
        Output ONLY the JSON object as a valid JSON string. Do NOT include any explanations or markdown.

        The user's original instruction was:
        {user_instruction}

        The MongoDB Schema is:
        {self.db_schema}

        The retrieved context was:
        {context}

        Your previous, erroneous output was:
        ---
        {{previous_llm_output}}
        ---
        The JSON parsing error was:
        {{json_error}}
        ---

        Corrected Output (JSON object as a string):
        """

        llm_output_text = ""
        json_error_for_retry = ""

        for attempt in range(self.max_retries + 1):
            current_prompt = ""
            if attempt == 0:
                current_prompt = initial_prompt
            else:
                current_prompt = retry_prompt_template.format(
                    previous_llm_output=llm_output_text,
                    json_error=json_error_for_retry
                )

            try:
                print(f"Tentativo {attempt + 1}")
                response = self.model.generate_content(current_prompt)
                llm_output_text = response.text.strip()

                llm_output_text = self.clean_llm_json_output(llm_output_text)

                try:
                    json.loads(llm_output_text)
                    print(f"Tentativo {attempt + 1} riuscito: JSON valido.")
                    print(llm_output_text)
                    return llm_output_text, None, context
                except json.JSONDecodeError as e:
                    json_error_for_retry = str(e)
                    if attempt < self.max_retries:
                        print(f"Tentativo {attempt + 1} fallito: JSON non valido. Errore: {json_error_for_retry}")
                        print(llm_output_text)
                        continue
                    else:
                        error_message = (f"L'output dell'LLM non era un JSON valido dopo {self.max_retries + 1} tentativi.\n"
                                         f"Ultimo errore JSON: {json_error_for_retry}\n"
                                         f"Ultimo Output LLM:\n---\n{llm_output_text}\n---")
                        print(error_message)
                        return None, error_message, context

            except Exception as e:
                error_message = f"Errore durante la generazione della query: {e}"
                print(error_message)
                return None, error_message, context

    def retrieve_context(self, user_instruction: str, n_results: int = 3) -> str:
        query_embedding = self.embedding_model.encode(user_instruction)
        results = self.chroma_collection.query(query_embeddings=[query_embedding], n_results=n_results, include=["documents", "metadatas", "distances"])
        documents = results["documents"][0]
        return "\n---\n".join(documents)

    def clean_llm_json_output(self, text: str) -> str:
        """
        Rimuove i blocchi di codice Markdown comuni (es. ```json ... ```) da una stringa.
        """
        text = text.strip()
        # Regex per catturare il contenuto all'interno di ```json ... ``` o ``` ... ```
        match = re.match(r"^\s*```(?:[a-zA-Z0-9]+)?\s*([\s\S]*?)\s*```\s*$", text)
        if match:
            # Se è stato trovato un blocco markdown, restituisce il contenuto catturato
            return match.group(1).strip()
        else:
            # Se nessun blocco markdown è rilevato, restituisce il testo originale (dopo strip)
            return text




