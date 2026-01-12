import os
from enum import Enum
from typing import List, Optional
from falkordb import FalkorDB
from llama_index.core import Document, PropertyGraphIndex, StorageContext
from llama_index.graph_stores.falkordb import FalkorDBGraphStore
from llama_index.core.indices.property_graph import SchemaLLMPathExtractor
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
    def __init__(self, graph_name: str = "enterprise_knowledge"):
        self.host = os.getenv("FALKORDB_HOST", "localhost")
        self.port = int(os.getenv("FALKORDB_PORT", 6379))
        self.graph_name = graph_name
        
        # Initialize FalkorDB Graph Store
        self.graph_store = FalkorDBGraphStore(
            host=self.host,
            port=self.port,
            graph_name=self.graph_name
        )
        self.storage_context = StorageContext.from_defaults(graph_store=self.graph_store)
        
        # LLM for Extraction
        self.llm = OpenAI(model="gpt-4o")
        
        # Schema Definition
        self.validation_schema = [
            (EntityType.DOCUMENT, RelationType.MENCIONA, EntityType.PROJECT),
            (EntityType.DOCUMENT, RelationType.TRATA_SOBRE, EntityType.TOPIC),
            (EntityType.DOCUMENT, RelationType.ESCRITO_POR, EntityType.AUTHOR),
            (EntityType.PROJECT, RelationType.LIDERADO_POR, EntityType.AUTHOR),
            (EntityType.PROJECT, RelationType.UTILIZA, EntityType.TECHNOLOGY),
        ]
        
        self.extractor = SchemaLLMPathExtractor(
            llm=self.llm,
            possible_entities=EntityType,
            possible_relations=RelationType,
            kg_validation_schema=self.validation_schema,
            strict=True
        )

    def index_documents(self, documents: List[Document]):
        """
        Processes documents, extracts the graph, and stores it in FalkorDB.
        """
        index = PropertyGraphIndex.from_documents(
            documents,
            storage_context=self.storage_context,
            kg_extractors=[self.extractor],
            show_progress=True
        )
        return index

    def query_graph(self, query_str: str):
        """
        Performs a query specifically on the graph.
        """
        index = PropertyGraphIndex.from_existing_index(self.storage_context)
        query_engine = index.as_query_engine(llm=self.llm)
        return query_engine.query(query_str)
