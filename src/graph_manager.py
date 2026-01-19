import os
from enum import Enum
from typing import List, Optional
from falkordb import FalkorDB
from llama_index.core import Document
from llama_index.llms.openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class EntityType(str, Enum):
    DOCUMENT = "Document"
    TOPIC = "Topic"
    PROJECT = "Project"
    TECHNOLOGY = "Technology"
    AUTHOR = "Author"


class RelationType(str, Enum):
    MENCIONA = "Menciona"
    LIDERADO_POR = "LideradoPor"
    UTILIZA = "Utiliza"
    TRATA_SOBRE = "TrataSobre"
    ESCRITO_POR = "EscritoPor"


class GraphManager:
    """
    Simplified Graph Manager using native FalkorDB connection.
    Extracts entities and relationships using LLM and stores them directly in FalkorDB.
    """

    def __init__(self, graph_name: str = "enterprise_knowledge"):
        self.host = os.getenv("FALKORDB_HOST", "localhost")
        self.port = int(os.getenv("FALKORDB_PORT", 6379))
        self.graph_name = graph_name

        # Native FalkorDB connection
        self.db = FalkorDB(host=self.host, port=self.port)
        self.graph = self.db.select_graph(graph_name)

        # LLM for extraction
        self.llm = OpenAI(model="gpt-4o", temperature=0)

    def index_documents(self, documents: List[Document]):
        """
        Extracts entities and relationships from documents using LLM prompting.
        """
        for doc in documents:
            self._extract_and_store(doc)
        return len(documents)

    def _extract_and_store(self, doc: Document):
        """
        Uses LLM to extract entities and stores them in FalkorDB.
        """
        extraction_prompt = f"""
Analiza el siguiente texto y extrae entidades y relaciones según este esquema:

ENTIDADES: Document, Topic, Project, Technology, Author
RELACIONES: Menciona, LideradoPor, Utiliza, TrataSobre, EscritoPor

Texto:
{doc.text[:1000]}

Responde SOLO con comandos Cypher para crear nodos y relaciones. Ejemplo:
MERGE (d:Document {{name: 'doc1'}})
MERGE (p:Project {{name: 'ProjectX'}})
MERGE (d)-[:Menciona]->(p)
"""

        try:
            response = self.llm.complete(extraction_prompt)
            cypher_commands = str(response).strip().split("\n")

            for command in cypher_commands:
                command = command.strip()
                if command and (
                    command.startswith("MERGE") or command.startswith("CREATE")
                ):
                    try:
                        self.graph.query(command)
                    except Exception as e:
                        print(f"Error executing Cypher: {command[:50]}... - {e}")
        except Exception as e:
            print(f"Error in LLM extraction: {e}")

    def query_graph(self, query_str: str) -> str:
        """
        Queries the graph for relevant relationships.
        """
        # Simple query to get recent relationships
        try:
            result = self.graph.query(
                "MATCH (n)-[r]->(m) RETURN type(r) as relation, labels(n)[0] as from_type, labels(m)[0] as to_type LIMIT 10"
            )

            if result.result_set:
                relations = []
                for row in result.result_set:
                    relations.append(f"{row[1]} -{row[0]}-> {row[2]}")
                return "Relaciones encontradas:\n" + "\n".join(relations)
            return "No se encontraron relaciones en el grafo."
        except Exception as e:
            return f"Error consultando el grafo: {e}"

    def delete_document_by_hash(self, file_hash: str):
        """Delete document nodes from graph by file hash"""
        try:
            # Delete nodes that have this file_hash property
            query = """
            MATCH (n:Document)
            WHERE n.file_hash = $file_hash
            DETACH DELETE n
            """
            result = self.graph.run(query, file_hash=file_hash)
            return True
        except Exception as e:
            print(f"Error deleting document from graph: {e}")
            return False

    def search_entities(self, name: str):
        """Search for entities by name"""
        query = f"MATCH (n) WHERE n.name CONTAINS '{name}' RETURN n.name as entity, labels(n)[0] as type"
        result = self.graph.query(query)
        if result.result_set:
            return [{"entity": row[0], "type": row[1]} for row in result.result_set]
        return []

    def get_graph_statistics(self):
        """Return basic statistics about the graph"""
        try:
            result1 = self.graph.query("MATCH (n) RETURN count(n)")
            result2 = self.graph.query("MATCH ()-[r]->() RETURN count(r)")
            return {
                "nodes": result1.result_set[0][0],
                "relationships": result2.result_set[0][0]
            }
        except:
            return {"nodes": 0, "relationships": 0}

    def create_relationship(self, entity1: str, entity2: str, relationship: str):
        """Create a relationship between two entities"""
        query = f"MATCH (a), (b) WHERE a.name = '{entity1}' AND b.name = '{entity2}' MERGE (a)-[:{relationship}]->(b)"
        self.graph.query(query)
