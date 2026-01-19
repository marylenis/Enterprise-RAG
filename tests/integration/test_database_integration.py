import os
import pytest
import asyncio
import tempfile
from unittest.mock import Mock, patch, MagicMock
import redis
from qdrant_client import QdrantClient
from falkordb import FalkorDB
from llama_index.core import Document
from qdrant_client.http.models import PointStruct
# import falkordb

# Import the actual modules we're testing
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.vector_store import VectorIndexManager
from src.graph_manager import GraphManager
from src.cache_manager import CacheManager
from src.embeddings import configure_embeddings_and_chunking


@pytest.fixture(scope="session")
def test_env_vars():
    """Set up test environment variables for databases"""
    original_env = {}
    test_vars = {
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "QDRANT_HOST": "localhost",
        "QDRANT_PORT": "6333",
        "FALKORDB_HOST": "localhost",
        "FALKORDB_PORT": "6380",
        "OPENAI_API_KEY": "test-key-for-integration-tests",
        "QDRANT_COLLECTION": "test_enterprise_docs",
        "FALKORDB_GRAPH": "test_enterprise_knowledge",
    }

    for key, value in test_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield test_vars

    # Restore original environment
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client"""
    mock_client = MagicMock(spec=redis.Redis)
    mock_client.ping.return_value = True
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = 1
    mock_client.keys.return_value = []
    mock_client.exists.return_value = False
    return mock_client


@pytest.fixture
def mock_qdrant_client():
    """Create a mock Qdrant client"""
    mock_client = MagicMock()
    mock_client.get_collections.return_value = Mock(collections=[])
    mock_client.create_collection.return_value = None
    mock_client.upsert.return_value = None
    mock_client.search.return_value = []
    mock_client.delete.return_value = None
    mock_client.get_collection.return_value = Mock(vectors_count=0)
    mock_client.collection_exists.return_value = True
    return mock_client


@pytest.fixture
def mock_falkordb_client():
    """Create a mock FalkorDB client (the graph object)"""
    mock_client = MagicMock()
    # Mock result object with result_set attribute
    mock_result = MagicMock()
    mock_result.result_set = [
        ["relation1", "TypeA", "TypeB"],
        ["relation2", "TypeC", "TypeD"]
    ]
    mock_client.query.return_value = mock_result
    mock_client.run.return_value = MagicMock()
    mock_client.execute_query.return_value = MagicMock()
    return mock_client


@pytest.fixture
def mock_falkordb_db(mock_falkordb_client):
    """Create a mock FalkorDB connection"""
    mock_db = MagicMock()
    mock_db.select_graph.return_value = mock_falkordb_client
    return mock_db


@pytest.fixture
def mock_embedding_model():
    """Create a mock embedding model"""
    mock_model = MagicMock()
    mock_model.get_text_embedding.return_value = [0.1, 0.2, 0.3] * 128
    mock_model.get_query_embedding.return_value = [0.1, 0.2, 0.3] * 128
    return mock_model


class TestRedisIntegration:
    """Test Redis caching functionality"""

    def test_redis_connection(self, mock_redis_client):
        """Test Redis connection establishment"""
        with patch("src.cache_manager.redis.Redis", return_value=mock_redis_client):
            cache_manager = CacheManager()
            cache_manager.redis_client = mock_redis_client

            # Test connection
            assert cache_manager.redis_client.ping() == True

    def test_cache_set_and_get(self, mock_redis_client):
        """Test basic cache set and get operations"""
        with patch("src.cache_manager.redis.Redis", return_value=mock_redis_client):
            cache_manager = CacheManager()
            cache_manager.redis_client = mock_redis_client

            # Mock serialization
            test_data = {"query": "test", "response": "cached response"}
            mock_redis_client.get.return_value = None  # Cache miss initially

            # Test cache miss
            result = cache_manager.get_cached_response("test query", "hybrid")
            assert result is None

            # Test cache set
            cache_manager.cache_response("test query", test_data, "hybrid")
            mock_redis_client.setex.assert_called()

            # Test cache hit
            import json

            mock_redis_client.get.return_value = json.dumps(test_data).encode()
            result = cache_manager.get_cached_response("test query", "hybrid")
            assert result == test_data

    def test_cache_invalidation(self, mock_redis_client):
        """Test cache invalidation"""
        with patch("src.cache_manager.redis.Redis", return_value=mock_redis_client):
            cache_manager = CacheManager()
            cache_manager.redis_client = mock_redis_client

            # Mock keys matching pattern
            mock_redis_client.keys.return_value = [
                b"cache:key1",
                b"cache:key2",
                b"cache:key3",
            ]
            mock_redis_client.delete.return_value = 3

            cleared_count = cache_manager.invalidate_cache("cache:*")
            assert cleared_count == 3
            mock_redis_client.keys.assert_called_with("cache:*")
            mock_redis_client.delete.assert_called()

    def test_cache_statistics(self, mock_redis_client):
        """Test cache statistics collection"""
        with patch("src.cache_manager.redis.Redis", return_value=mock_redis_client):
            cache_manager = CacheManager()
            cache_manager.redis_client = mock_redis_client

            # Mock info response
            mock_redis_client.info.return_value = {
                "keyspace_hits": 100,
                "keyspace_misses": 50,
            }

            stats = cache_manager.get_cache_stats()
            assert "total_accesses" in stats
            assert "hit_rate_percent" in stats
            assert "total_cached_queries" in stats

    def test_cache_error_handling(self, mock_redis_client):
        """Test cache error handling"""
        with patch("src.cache_manager.redis.Redis", return_value=mock_redis_client):
            cache_manager = CacheManager()
            cache_manager.redis_client = mock_redis_client

            # Simulate Redis connection error
            mock_redis_client.get.side_effect = redis.ConnectionError(
                "Connection failed"
            )

            # Should handle error gracefully
            result = cache_manager.get_cached_response("test query", "hybrid")
            assert result is None  # Should return None on error

    def test_cache_ttl_expiration(self, mock_redis_client):
        """Test cache TTL (time to live) functionality"""
        with patch("src.cache_manager.redis.Redis", return_value=mock_redis_client):
            cache_manager = CacheManager()
            cache_manager.redis_client = mock_redis_client

            test_data = {"query": "test", "response": "response"}

            # Test cache set with TTL
            cache_manager.cache_response("test query", test_data, "hybrid", ttl=3600)

            # Verify setex was called (set with expiration)
            assert mock_redis_client.setex.called or mock_redis_client.set.called


class TestQdrantIntegration:
    """Test Qdrant vector database integration"""

    def test_qdrant_client_creation(self, mock_qdrant_client):
        """Test Qdrant client creation and configuration"""
        with patch("src.vector_store.QdrantClient", return_value=mock_qdrant_client):
            manager = VectorIndexManager(collection_name="test_collection")
            manager.client = mock_qdrant_client

            assert manager.collection_name == "test_collection"
            assert manager.client == mock_qdrant_client

    def test_collection_creation(self, mock_qdrant_client):
        """Test collection creation with proper parameters"""
        with patch("src.vector_store.QdrantClient", return_value=mock_qdrant_client):
            mock_qdrant_client.get_collections.return_value = Mock(collections=[])
            mock_qdrant_client.collection_exists.return_value = False
    
            manager = VectorIndexManager(collection_name="test_collection")
            manager.client = mock_qdrant_client
    
            # Simulate collection creation
            manager._ensure_collection_exists()
    
            # Verify collection was created with correct parameters
            mock_qdrant_client.create_collection.assert_called_once()
            call_args = mock_qdrant_client.create_collection.call_args
            assert call_args[1]["collection_name"] == "test_collection"
            assert "vectors_config" in call_args[1]

    def test_vector_insertion(self, mock_qdrant_client):
        """Test vector insertion into Qdrant"""
        with patch("src.vector_store.QdrantClient", return_value=mock_qdrant_client):
            manager = VectorIndexManager(collection_name="test_collection")
            manager.client = mock_qdrant_client

            # Test data
            points = [
                PointStruct(
                    id=1,
                    vector=[0.1, 0.2, 0.3] * 128,
                    payload={"text": "sample text", "source": "test.txt"},
                )
            ]

            # Insert vectors
            mock_qdrant_client.upsert.return_value = None
            manager.insert_vectors(points)

            # Verify insertion
            mock_qdrant_client.upsert.assert_called_once_with(
                collection_name="test_collection", points=points
            )

    def test_vector_search(self, mock_qdrant_client):
        """Test vector search functionality"""
        with patch("src.vector_store.QdrantClient", return_value=mock_qdrant_client):
            manager = VectorIndexManager(collection_name="test_collection")
            manager.client = mock_qdrant_client

            # Mock search response
            mock_results = [
                Mock(
                    id=1,
                    score=0.95,
                    payload={"text": "matching document", "source": "test.txt"},
                ),
                Mock(
                    id=2,
                    score=0.87,
                    payload={"text": "another document", "source": "test2.txt"},
                ),
            ]
            mock_qdrant_client.search.return_value = mock_results

            # Perform search
            query_vector = [0.1, 0.2, 0.3] * 128
            results = manager.search_vectors(query_vector, limit=5)

            # Verify search was called correctly
            mock_qdrant_client.search.assert_called_once()
            
            # Verify results
            assert len(results) == 2

    def test_document_deletion(self, mock_qdrant_client):
        """Test document deletion from vector store"""
        with patch("src.vector_store.QdrantClient", return_value=mock_qdrant_client):
            manager = VectorIndexManager(collection_name="test_collection")
            manager.client = mock_qdrant_client

            # Delete document by hash
            document_hash = "abc123def456"
            manager.delete_document(document_hash)

            # Verify deletion was called with proper filter
            mock_qdrant_client.delete.assert_called_once()

    def test_collection_info(self, mock_qdrant_client):
        """Test getting collection information"""
        with patch("src.vector_store.QdrantClient", return_value=mock_qdrant_client):
            manager = VectorIndexManager(collection_name="test_collection")
            manager.client = mock_qdrant_client

            # Mock collection info
            mock_qdrant_client.get_collection.return_value = MagicMock(vectors_count=100)

            info = manager.get_collection_info()
            assert info["vectors_count"] == 100

    def test_qdrant_error_handling(self, mock_qdrant_client):
        """Test Qdrant error handling"""
        with patch("src.vector_store.QdrantClient", return_value=mock_qdrant_client):
            manager = VectorIndexManager(collection_name="test_collection")
            manager.client = mock_qdrant_client

            # Simulate connection error
            mock_qdrant_client.search.side_effect = Exception("Connection failed")

            # Should handle error gracefully
            query_vector = [0.1, 0.2, 0.3] * 128
            with pytest.raises(Exception):
                manager.search_vectors(query_vector)


class TestFalkorDBIntegration:
    """Test FalkorDB graph database integration"""

    def test_falkordb_connection(self, mock_falkordb_db, mock_falkordb_client):
        """Test FalkorDB connection establishment"""
        with patch(
            "src.graph_manager.FalkorDB", return_value=mock_falkordb_db
        ):
            graph_manager = GraphManager(graph_name="test_graph")
            assert graph_manager.graph_name == "test_graph"
            assert graph_manager.graph == mock_falkordb_client

    def test_entity_extraction_and_indexing(self, mock_falkordb_db, mock_falkordb_client):
        """Test entity extraction and indexing"""
        from llama_index.core import Document
        with patch(
            "src.graph_manager.FalkorDB", return_value=mock_falkordb_db
        ):
            graph_manager = GraphManager(graph_name="test_graph")

            # Mock documents
            documents = [
                Document(
                    text="Apple Inc. is a technology company founded by Steve Jobs.",
                    metadata={"source": "test.txt"},
                )
            ]
    
            # 2. Extract entities and store in graph DB
            with patch("llama_index.llms.openai.OpenAI.complete") as mock_complete:
                # Mock return value to behave like a string for str() call
                mock_response = MagicMock(text="MERGE (n:Company {name: 'Apple Inc.'})")
                mock_response.__str__.return_value = "MERGE (n:Company {name: 'Apple Inc.'})"
                mock_complete.return_value = mock_response
                graph_manager.index_documents(documents)
                
                # Mock query result
                mock_result = MagicMock()
                mock_result.result_set = []
                mock_falkordb_client.query.return_value = mock_result
                
                # Index documents (already called above, but test logic repeats)
                graph_manager.index_documents(documents)
    
                # Verify queries were executed
                assert mock_falkordb_client.query.call_count > 0

    def test_entity_relationship_creation(self, mock_falkordb_db, mock_falkordb_client):
        """Test entity relationship creation (B7 fix)"""
        with patch(
            "src.graph_manager.FalkorDB", return_value=mock_falkordb_db
        ):
            graph_manager = GraphManager(graph_name="test_graph")
            
            # Create relationship
            graph_manager.create_relationship("Apple Inc.", "Steve Jobs", "FOUNDED_BY")
            
            # Verify query
            assert mock_falkordb_client.query.call_count > 0

    def test_graph_search(self, mock_falkordb_db, mock_falkordb_client):
        """Test graph search functionality"""
        with patch(
            "src.graph_manager.FalkorDB", return_value=mock_falkordb_db
        ):
            graph_manager = GraphManager(graph_name="test_graph")
            
            # Mock search results as an object with result_set
            mock_result = MagicMock()
            mock_result.result_set = [
                ["Apple Inc.", "Company"],
                ["Steve Jobs", "Person"],
            ]
            mock_falkordb_client.query.return_value = mock_result
            
            # Search for entities
            results = graph_manager.search_entities("Apple")

            # Verify search was executed
            mock_falkordb_client.query.assert_called()
            assert len(results) == 2

    def test_document_deletion_from_graph(self, mock_falkordb_db, mock_falkordb_client):
        """Test document deletion from graph store"""
        with patch(
            "src.graph_manager.FalkorDB", return_value=mock_falkordb_db
        ):
            graph_manager = GraphManager(graph_name="test_graph")

            # Delete document by hash
            document_hash = "abc123def456"
            graph_manager.delete_document_by_hash(document_hash)

            # Verify deletion query was executed
            mock_falkordb_client.run.assert_called()

    def test_graph_statistics(self, mock_falkordb_db, mock_falkordb_client):
        """Test graph statistics collection"""
        with patch(
            "src.graph_manager.FalkorDB", return_value=mock_falkordb_db
        ):
            graph_manager = GraphManager(graph_name="test_graph")

            # Mock statistics response (two queries)
            mock_result_nodes = MagicMock()
            mock_result_nodes.result_set = [[150]]
            mock_result_rels = MagicMock()
            mock_result_rels.result_set = [[200]]
            
            mock_falkordb_client.query.side_effect = [mock_result_nodes, mock_result_rels]

            stats = graph_manager.get_graph_statistics()

            # Verify statistics query
            mock_falkordb_client.query.assert_called()
            assert stats["nodes"] == 150
            assert stats["relationships"] == 200


class TestEmbeddingIntegration:
    """Test embedding generation and configuration"""

    def test_embedding_configuration(self):
        """Test embedding model configuration (B8 fix)"""
        from llama_index.core.embeddings import BaseEmbedding
        
        class MockEmbeddingModel(BaseEmbedding):
            model_name: str = "text-embedding-3-small"
            def _get_query_embedding(self, query: str): return [0.1]*1536
            def _get_text_embedding(self, text: str): return [0.1]*1536
            def _aget_query_embedding(self, query: str): return [0.1]*1536
            def _aget_text_embedding(self, text: str): return [0.1]*1536
        
        with patch("src.embeddings.OpenAIEmbedding") as mock_openai_embed:
            mock_embed = MockEmbeddingModel()
            mock_openai_embed.return_value = mock_embed
    
            embed_model, parser = configure_embeddings_and_chunking()
            
            assert embed_model.model_name == "text-embedding-3-small"
            assert parser.chunk_size == 500

    def test_embedding_generation(self, mock_embedding_model):
        """Test embedding generation for text"""
        # Mock OpenAIEmbedding because src.embeddings uses it
        with patch(
            "src.embeddings.OpenAIEmbedding", return_value=mock_embedding_model
        ):
            model = mock_embedding_model

            # Generate embeddings
            text = "This is a test document"
            embedding = model.get_text_embedding(text)

            # Verify embeddings were generated
            assert len(embedding) > 0
            mock_embedding_model.get_text_embedding.assert_called_once_with(text)


class TestDatabaseIntegrationScenarios:
    """Test integration scenarios between multiple databases"""

    def test_vector_graph_data_flow(self, mock_qdrant_client, mock_falkordb_db, mock_falkordb_client):
        """Test data flow between vector and graph databases"""
        with (
            patch("src.vector_store.QdrantClient", return_value=mock_qdrant_client),
            patch(
                "src.graph_manager.FalkorDB", return_value=mock_falkordb_db
            ),
        ):
            vector_manager = VectorIndexManager(collection_name="test_collection")
            graph_manager = GraphManager(graph_name="test_graph")

            # Simulate document processing
            document_text = "Apple Inc. is a technology company founded by Steve Jobs."
            documents = [Document(text=document_text, metadata={"source": "test.txt"})]

            # 1. Generate embeddings and store in vector DB
            query_vector = [0.1, 0.2, 0.3] * 128
            mock_qdrant_client.search.return_value = []

            vector_manager.search_vectors(query_vector)

            # 2. Extract entities and store in graph DB
            with patch("llama_index.llms.openai.OpenAI.complete") as mock_complete:
                # Mock return value to behave like a string for str() call
                mock_response = MagicMock(text="MERGE (n:Company {name: 'Apple Inc.'})")
                mock_response.__str__.return_value = "MERGE (n:Company {name: 'Apple Inc.'})"
                mock_complete.return_value = mock_response
                
                graph_manager.index_documents(documents)
    
            # Verify both databases were called
            mock_qdrant_client.search.assert_called_once()
            mock_falkordb_client.query.assert_called()

    def test_cache_database_cooperation(self, mock_redis_client, mock_qdrant_client):
        """Test cooperation between cache and databases"""
        with (
            patch("src.cache_manager.redis.Redis", return_value=mock_redis_client),
            patch("src.vector_store.QdrantClient", return_value=mock_qdrant_client),
        ):
            cache_manager = CacheManager()
            vector_manager = VectorIndexManager(collection_name="test_collection")

            cache_manager.redis_client = mock_redis_client
            vector_manager.client = mock_qdrant_client

            query = "What is Apple Inc.?"

            # 1. Check cache first
            mock_redis_client.get.return_value = None
            cached_result = cache_manager.get_cached_response(query, "hybrid")
            assert cached_result is None

            # 2. Search vector database
            mock_qdrant_client.search.return_value = [
                Mock(score=0.95, payload={"text": "Apple Inc. is a technology company"})
            ]
            vector_manager.search_vectors([0.1, 0.2, 0.3] * 128)

            # 3. Cache the results
            response_data = {"query": query, "response": "Apple Inc. is a company"}
            cache_manager.cache_response(query, response_data, "hybrid")

            # Verify all operations
            mock_redis_client.get.assert_called()
            mock_qdrant_client.search.assert_called()
            mock_redis_client.setex.assert_called()

    def test_consistent_document_deletion(
        self, mock_qdrant_client, mock_falkordb_db, mock_falkordb_client, mock_redis_client
    ):
        """Test consistent document deletion across all stores"""
        with (
            patch("src.vector_store.QdrantClient", return_value=mock_qdrant_client),
            patch(
                "src.graph_manager.FalkorDB", return_value=mock_falkordb_db
            ),
            patch("src.cache_manager.redis.Redis", return_value=mock_redis_client),
        ):
            vector_manager = VectorIndexManager(collection_name="test_collection")
            graph_manager = GraphManager(graph_name="test_graph")
            cache_manager = CacheManager()

            document_hash = "abc123def456"

            # Delete from all stores
            mock_redis_client.keys.return_value = ["test_key"]
            vector_manager.delete_document(document_hash)
            graph_manager.delete_document_by_hash(document_hash)
            cache_manager.invalidate_cache(f"*{document_hash}*")

            # Verify all deletion operations
            mock_qdrant_client.delete.assert_called_once()
            mock_falkordb_client.run.assert_called()
            mock_redis_client.keys.assert_called()
            # Redis delete takes the result of keys()
            mock_redis_client.delete.assert_called()
