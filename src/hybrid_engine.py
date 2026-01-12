from typing import List, Optional
from llama_index.core import Settings, PromptTemplate
from llama_index.core.query_engine import CustomQueryEngine
from src.graph_manager import GraphManager

class HybridQueryEngine(CustomQueryEngine):
    """
    Motor de consulta híbrido que combina búsqueda vectorial y travesía de grafos.
    """
    vector_index: any
    graph_manager: GraphManager
    
    def __init__(self, vector_index, graph_manager: GraphManager):
        super().__init__(vector_index=vector_index, graph_manager=graph_manager)

    def custom_query(self, query_str: str):
        # 1. Recuperación Vectorial (Hechos y Contexto Semántico)
        retriever = self.vector_index.as_retriever(similarity_top_k=3)
        nodes = retriever.retrieve(query_str)
        vector_context = "\n".join([f"[Fuente: {n.metadata.get('file_path')}] {n.text}" for n in nodes])
        
        # 2. Recuperación de Grafo (Relaciones y Estructura)
        # Usamos el motor de consulta del grafo para obtener relaciones relevantes
        graph_response = self.graph_manager.query_graph(query_str)
        graph_context = str(graph_response)
        
        # 3. Combinación de Contexto
        full_context = (
            "--- CONTEXTO VECTORIAL ---\n"
            f"{vector_context}\n\n"
            "--- RELACIONES DEL GRAFO ---\n"
            f"{graph_context}"
        )
        
        # 4. Generación de Respuesta Final
        prompt = self._get_hybrid_prompt()
        response = Settings.llm.complete(prompt.format(context_str=full_context, query_str=query_str))
        return response

    def _get_hybrid_prompt(self):
        template = (
            "Eres un experto analista de documentación técnica.\n"
            "Tu tarea es responder preguntas combinando hechos textuales (Vectorial) con relaciones entre entidades (Grafo).\n\n"
            "REGLAS:\n"
            "1. Si el grafo muestra una relación entre un Autor y un Proyecto, menciónalo explícitamente.\n"
            "2. Usa el contexto vectorial para dar detalles específicos sobre el contenido de los documentos.\n"
            "3. Si hay contradicciones, prioriza los documentos más recientes.\n"
            "4. Cita siempre las fuentes si están disponibles.\n\n"
            "Contexto:\n{context_str}\n\n"
            "Pregunta: {query_str}\n\n"
            "Respuesta Estructurada:"
        )
        return PromptTemplate(template)
