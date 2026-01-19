import os
import pytest
import tempfile
import shutil
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "docker: marks tests that require docker")
    config.addinivalue_line(
        "markers", "database: marks tests that require database connections"
    )


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment for all tests"""
    # Set test environment variables
    original_env = {}
    test_env = {
        "TESTING": "true",
        "INTEGRATION_TEST": "true",
        "OPENAI_API_KEY": "test-key-for-testing",
        "PYTHONPATH": os.path.join(os.path.dirname(__file__), ".."),
        "QDRANT_COLLECTION": "test_enterprise_docs",
        "FALKORDB_GRAPH": "test_enterprise_knowledge",
    }

    # Store original values and set test values
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield test_env

    # Restore original environment
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture(scope="function")
def temp_directory():
    """Create a temporary directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def mock_openai_client():
    """Mock OpenAI client for testing"""
    with pytest.MonkeyPatch().context() as m:
        # Mock OpenAI embedding model
        mock_embed = Mock()
        mock_embed.model_name = "text-embedding-3-small"
        mock_embed.get_query_embedding.return_value = [0.1, 0.2, 0.3] * 128
        mock_embed.get_text_embedding.return_value = [0.1, 0.2, 0.3] * 128
        mock_embed.get_text_embeddings.return_value = [[0.1, 0.2, 0.3] * 128]

        m.setattr("src.embeddings.OpenAIEmbedding", lambda **kwargs: mock_embed)
        yield mock_embed


@pytest.fixture(scope="function")
def sample_documents():
    """Sample documents for testing"""
    return [
        {
            "text": "Apple Inc. is a technology company headquartered in Cupertino, California.",
            "metadata": {"source": "company_info.txt", "type": "company"},
        },
        {
            "text": "The iPhone is a line of smartphones designed and marketed by Apple Inc.",
            "metadata": {"source": "products.md", "type": "product"},
        },
        {
            "text": "Steve Jobs co-founded Apple Inc. in 1976 along with Steve Wozniak.",
            "metadata": {"source": "history.txt", "type": "history"},
        },
    ]


@pytest.fixture(scope="function")
def sample_queries():
    """Sample queries for testing"""
    return [
        "What is Apple Inc.?",
        "What products does Apple make?",
        "Who founded Apple Inc.?",
        "Where is Apple headquartered?",
        "When was Apple founded?",
    ]


@pytest.fixture(scope="function")
def mock_responses():
    """Mock API responses for testing"""
    return {
        "health": {"status": "healthy", "service": "Enterprise RAG"},
        "query": {
            "query": "What is Apple?",
            "response": "Apple Inc. is a technology company",
            "sources": ["company_info.txt"],
        },
        "ingest": {"status": "success", "files_processed": 3},
        "audit": [
            {
                "file_path": "test.txt",
                "version": 1,
                "author": "TestUser",
                "timestamp": "2024-01-01T12:00:00Z",
                "status": "created",
            }
        ],
        "cache_stats": {"hits": 10, "misses": 5, "hit_rate": 0.67},
        "error": {"detail": "Test error message"},
    }


@pytest.fixture(scope="session")
def test_timeout():
    """Default timeout for integration tests"""
    return 30


# Database connection fixtures
@pytest.fixture(scope="session")
def redis_config():
    """Redis configuration for testing"""
    return {
        "host": os.environ.get("REDIS_HOST", "localhost"),
        "port": int(os.environ.get("REDIS_PORT", "6379")),
        "db": 1,  # Use test database
        "decode_responses": True,
    }


@pytest.fixture(scope="session")
def qdrant_config():
    """Qdrant configuration for testing"""
    return {
        "host": os.environ.get("QDRANT_HOST", "localhost"),
        "port": int(os.environ.get("QDRANT_PORT", "6333")),
        "collection_prefix": "test_",
    }


@pytest.fixture(scope="session")
def falkordb_config():
    """FalkorDB configuration for testing"""
    return {
        "host": os.environ.get("FALKORDB_HOST", "localhost"),
        "port": int(os.environ.get("FALKORDB_PORT", "6380")),
        "graph_prefix": "test_",
    }


class UnifiedMockContainer:
    """A simple container that supports both attribute and dictionary access to pre-configured mocks"""
    def __init__(self, **mocks):
        self._mocks = mocks
        for name, mock_obj in mocks.items():
            setattr(self, name, mock_obj)
            
    def __getitem__(self, key):
        if key in self._mocks:
            return self._mocks[key]
        raise KeyError(key)
    
    def __getattr__(self, name):
        if name in self._mocks:
            return self._mocks[name]
        raise AttributeError(name)

@pytest.fixture
def mock_containers():
    """Combined mock for all controllers using dependency_overrides"""
    from src.main import (
        get_hybrid_engine,
        get_vector_only_engine,
        get_vector_manager,
        get_graph_manager,
        app,
    )

    # 1. Create robust sub-mocks
    mock_hybrid_engine = MagicMock()
    mock_vector_engine = MagicMock()
    mock_vector_manager = MagicMock()
    mock_graph_manager = MagicMock()
    mock_audit_manager = MagicMock()

    # 2. Configure default behaviors to cover most tests
    mock_hybrid_engine.custom_query.return_value = "Test response"
    mock_hybrid_engine.query.return_value = "Test response" # Some tests might use .query
    
    mock_vector_engine.query.return_value = "Test response"
    
    mock_vector_manager.index_documents.return_value = 1
    mock_vector_manager.search_vectors.return_value = []
    mock_vector_manager.delete_document.return_value = True
    mock_vector_manager.audit_manager = mock_audit_manager
    
    mock_graph_manager.index_documents.return_value = True
    mock_graph_manager.search_entities.return_value = []
    mock_graph_manager.delete_document_by_hash.return_value = True
    
    mock_audit_manager.get_audit_log.return_value = [
        {
            "file_path": "/test/file.txt",
            "hash": "abc123",
            "author": "Test User",
            "timestamp": "2024-01-01 00:00:00",
            "version": 1,
            "is_active": True,
            "status": "created"
        }
    ]

    # 3. Set up FastAPI dependency overrides
    app.dependency_overrides[get_hybrid_engine] = lambda: mock_hybrid_engine
    app.dependency_overrides[get_vector_only_engine] = lambda: mock_vector_engine
    app.dependency_overrides[get_vector_manager] = lambda: mock_vector_manager
    app.dependency_overrides[get_graph_manager] = lambda: mock_graph_manager

    # 4. Wrap in UnifiedMockContainer
    container = UnifiedMockContainer(
        hybrid_engine=mock_hybrid_engine,
        vector_only_engine=mock_vector_engine,
        vector_engine=mock_vector_engine, # Alias for consistency
        vector_manager=mock_vector_manager,
        graph_manager=mock_graph_manager,
        audit_manager=mock_audit_manager
    )

    yield container

    # 5. Clean up overrides
    app.dependency_overrides = {}

@pytest.fixture
def mock_controllers(mock_containers):
    """Alias for mock_containers for backward compatibility"""
    return mock_containers


@pytest.fixture
def cache_manager():
    """Mock cache manager fixture"""
    from src.main import cache_manager as actual_cache
    with patch("src.main.cache_manager", wraps=actual_cache) as mock_cache:
        mock_cache.get_cached_response.return_value = None
        yield mock_cache


@pytest.fixture
def cost_optimizer():
    """Mock cost optimizer fixture"""
    from src.main import cost_optimizer as actual_optimizer
    with patch("src.main.cost_optimizer", wraps=actual_optimizer) as mock_optimizer:
        mock_optimizer.track_request_cost.return_value = None
        mock_optimizer.get_cost_stats.return_value = {
            "total_cost": 0.05,
            "total_requests": 100,
            "average_cost": 0.0005,
            "total_tokens_input": 50000,
            "total_tokens_output": 75000,
            "cache_hit_rate": 0.2
        }
        # Mock token manager
        mock_optimizer.token_manager = MagicMock()
        mock_optimizer.token_manager.track_tokens.return_value = {
            "allowed": True,
            "reason": None
        }
        yield mock_optimizer


# Integration test utilities
class IntegrationTestHelper:
    """Helper class for integration tests"""

    @staticmethod
    def create_test_files(directory: str, files: Dict[str, str]):
        """Create test files in directory"""
        for filename, content in files.items():
            file_path = os.path.join(directory, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

    @staticmethod
    def cleanup_test_data(
        redis_config: dict, qdrant_config: dict, falkordb_config: dict
    ):
        """Clean up test data from databases"""
        try:
            # Clean Redis
            import redis

            redis_client = redis.Redis(**redis_config)
            redis_client.flushdb()
        except:
            pass

        try:
            # Clean Qdrant collections
            from qdrant_client import QdrantClient

            qdrant_client = QdrantClient(
                host=qdrant_config["host"], port=qdrant_config["port"]
            )
            collections = qdrant_client.get_collections()
            for collection in collections.collections:
                if collection.name.startswith(qdrant_config["collection_prefix"]):
                    qdrant_client.delete_collection(collection.name)
        except:
            pass

        try:
            # Clean FalkorDB graphs
            import falkordb

            graph = falkordb.Graph(
                host=falkordb_config["host"], port=falkordb_config["port"]
            )
            # Delete test nodes
            graph.query("MATCH (n) WHERE n.test = true DELETE n")
        except:
            pass


@pytest.fixture
def integration_helper():
    """Integration test helper fixture"""
    return IntegrationTestHelper()


# Performance testing utilities
class PerformanceTracker:
    """Track performance during tests"""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.memory_usage = []

    def start(self):
        """Start performance tracking"""
        import time

        self.start_time = time.time()

    def stop(self):
        """Stop performance tracking"""
        import time

        self.end_time = time.time()

    @property
    def duration(self):
        """Get duration of tracked operation"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    def track_memory(self):
        """Track memory usage"""
        try:
            import psutil

            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_usage.append(memory_mb)
        except ImportError:
            pass


@pytest.fixture
def performance_tracker():
    """Performance tracking fixture"""
    return PerformanceTracker()


# Mock data generators
class MockDataGenerator:
    """Generate mock data for testing"""

    @staticmethod
    def generate_document(length: int = 100) -> str:
        """Generate mock document text"""
        sentences = [
            "This is a test document for the Enterprise RAG system.",
            "The system provides advanced document retrieval capabilities.",
            "Integration testing ensures all components work together correctly.",
            "Machine learning models power the search functionality.",
            "Documents are processed and indexed for efficient retrieval.",
        ]

        result = ""
        while len(result) < length:
            result += " ".join(sentences) + " "

        return result[:length]

    @staticmethod
    def generate_query() -> str:
        """Generate mock query"""
        queries = [
            "What are the main components of the system?",
            "How does document processing work?",
            "What databases are used?",
            "Explain the search functionality",
            "What are the system requirements?",
        ]
        import random

        return random.choice(queries)


@pytest.fixture
def mock_data_generator():
    """Mock data generator fixture"""
    return MockDataGenerator()
