import os
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from qdrant_client.http import models
from src.vector_store import VectorIndexManager
from src.embeddings import configure_embeddings_and_chunking
from dotenv import load_dotenv

load_dotenv()

class RAGQueryEngine:
    def __init__(self, collection_name: str = "enterprise_docs"):
        # Ensure embeddings are configured
        configure_embeddings_and_chunking()
        
        # Configure LLM
        self.llm = OpenAI(
            model="gpt-4o", # Using gpt-4o as default high-performance model
            api_key=os.getenv("OPENAI_API_KEY")
        )
        Settings.llm = self.llm
        
        # Initialize Vector Store
        self.vector_manager = VectorIndexManager(collection_name=collection_name)
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_manager.vector_store
        )

    def query(self, query_text: str, only_active: bool = True):
        """
        Executes a RAG query.
        By default, only searches for active (latest) document versions.
        """
        # Define filters for Qdrant
        filters = None
        if only_active:
            filters = models.Filter(
                must=[
                    models.FieldCondition(
                        key="is_active",
                        match=models.MatchValue(value=True)
                    )
                ]
            )

        # Create the retriever with filters
        query_engine = self.index.as_query_engine(
            vector_store_kwargs={"filter": filters},
            similarity_top_k=5,
            streaming=True # Enable streaming for better UX later on
        )

        # Custom system prompt for citation
        query_engine.update_prompts({
            "response_synthesizer:text_qa_template": self._get_custom_prompt()
        })

        response = query_engine.query(query_text)
        return response

    def _get_custom_prompt(self):
        """ Returns a custom prompt that enforces citation and accuracy. """
        from llama_index.core import PromptTemplate
        
        template = (
            "Eres un asistente virtual experto en documentación técnica empresarial.\n"
            "Tu objetivo es responder de manera precisa basándote ÚNICAMENTE en el contexto proporcionado.\n"
            "REGLAS CRÍTICAS:\n"
            "1. Si no encuentras la respuesta en el contexto, di 'No tengo información suficiente en los documentos'.\n"
            "2. DEBES citar la fuente para cada afirmación importante usando el nombre del archivo y la página si está disponible.\n"
            "3. Estructura tu respuesta con puntos clave para facilitar la lectura.\n\n"
            "Contexto:\n{context_str}\n\n"
            "Pregunta: {query_str}\n\n"
            "Respuesta (incluyendo citas):"
        )
        return PromptTemplate(template)

if __name__ == "__main__":
    # Test query engine
    engine = RAGQueryEngine()
    # response = engine.query("¿Qué servicios están configurados?")
    # print(response)
    print("Motor de consulta inicializado y listo.")
