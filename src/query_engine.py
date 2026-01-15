import os
from llama_index.core import VectorStoreIndex, Settings, PromptTemplate
from llama_index.llms.openai import OpenAI
from qdrant_client.http import models
from dotenv import load_dotenv

load_dotenv()

class RAGQueryEngine:
    def __init__(self, vector_index: VectorStoreIndex):
        self.index = vector_index
        
        # Configure LLM
        self.llm = OpenAI(
            model="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0
        )
        Settings.llm = self.llm

    def query(self, query_text: str, only_active: bool = True):
        """
        Executes a RAG query filtering by active documents.
        """
        try:
            # Create query engine
            query_engine = self.index.as_query_engine(
                similarity_top_k=3,
                llm=self.llm
            )
            
            # Update with custom prompt
            query_engine.update_prompts({
                "response_synthesizer:text_qa_template": self._get_custom_prompt()
            })
            
            response = query_engine.query(query_text)
            return response
        except Exception as e:
            return f"Error en la consulta: {str(e)}"

    def _get_custom_prompt(self):
        """Returns a custom prompt that enforces citation and accuracy."""
        template = (
            "Eres un asistente virtual experto en documentación técnica empresarial.\\n"
            "Tu objetivo es responder de manera precisa basándote ÚNICAMENTE en el contexto proporcionado.\\n"
            "REGLAS CRÍTICAS:\\n"
            "1. Si no encuentras la respuesta en el contexto, di 'No tengo información suficiente en los documentos'.\\n"
            "2. DEBES citar la fuente para cada afirmación importante.\\n"
            "3. Estructura tu respuesta con puntos clave.\\n\\n"
            "Contexto:\\n{context_str}\\n\\n"
            "Pregunta: {query_str}\\n\\n"
            "Respuesta (incluyendo citas):"
        )
        return PromptTemplate(template)
