from dependency_injector import containers, providers
from src.vector_store import VectorIndexManager
from src.graph_manager import GraphManager
from src.hybrid_engine import HybridQueryEngine
from src.query_engine import RAGQueryEngine
import os

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Managers
    vector_manager = providers.Singleton(
        VectorIndexManager,
        collection_name=os.getenv("QDRANT_COLLECTION", "enterprise_docs")
    )
    
    graph_manager = providers.Singleton(
        GraphManager,
        graph_name=os.getenv("FALKORDB_GRAPH", "enterprise_knowledge")
    )

    # Engines
    hybrid_engine = providers.Factory(
        HybridQueryEngine,
        vector_index=providers.Callable(lambda vm: vm.get_index(), vector_manager),
        graph_manager=graph_manager
    )
    
    vector_only_engine = providers.Factory(
        RAGQueryEngine,
        vector_index=providers.Callable(lambda vm: vm.get_index(), vector_manager)
    )
