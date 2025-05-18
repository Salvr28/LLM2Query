import tqdm
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import google.generativeai as genai


class MongoDBQueryGenerator:
    def __init__(self, embedding_model: SentenceTransformer, model: genai.GenerativeModel, chroma_client: chromadb.PersistentClient, db_schema):
        self.model = model
        self.chroma_client = chroma_client
        self.chroma_collection = self.chroma_client.get_collection(name="datasets_documentations")
        self.embedding_model = embedding_model
        self.db_schema = db_schema

    def generate_query(self, user_instruction: str) -> str:

        context = self.retrieve_context(user_instruction)

        prompt = f"""<s>
        Task Description:
        Your task is to create a MongoDB query that accurately fulfills the provided Instruct.
        The query MUST be in the format `db.CollectionName.operation(filter, projection, ...)` for read operations.
        DO NOT generate aggregation pipelines (i.e., do NOT start the output with `[` or use aggregation stages).
        Only use `find()` or `aggregate()` as the operation.
        Ensure all field names strictly adhere to the given MongoDB Schema.
        IMPORTANT: DO NOT wrap the query in any markdown code blocks (e.g., \`\`\`mongodb, \`\`\`json, \`\`\`javascript, or just \`\`\` ).
        Output ONLY the query string, nothing else.
        
        MongoDB Schema:
        {self.db_schema}

        Retrieved Context:
        {context}

        ### Instruct:
        {user_instruction}

        ### Output:
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip(), context
        except Exception as e:
            return f"Errore durante la generazione della query: {e}", context
    
    def retrieve_context(self, user_instruction: str, n_results: int = 3) -> str:
        query_embedding = self.embedding_model.encode(user_instruction)
        results = self.chroma_collection.query(query_embeddings=[query_embedding], n_results=n_results, include=["documents", "metadatas", "distances"])
        documents = results["documents"][0]
        return "\n---\n".join(documents)
    
    