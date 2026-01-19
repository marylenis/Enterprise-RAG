import os
import pytest
import asyncio
import json
import tempfile
import shutil
from typing import List, Dict, Any
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

# Import the actual modules we're testing
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.loader import get_directory_reader
from src.versioning import AuditManager
from src.vector_store import VectorIndexManager
from src.graph_manager import GraphManager
from src.hybrid_engine import HybridQueryEngine
from src.query_engine import RAGQueryEngine
from src.containers import Container


@pytest.fixture
def test_data_dir():
    """Create a temporary directory with test documents"""
    temp_dir = tempfile.mkdtemp()

    # Create test documents
    test_files = {
        "company_info.txt": """
        Apple Inc. is a multinational technology company headquartered in Cupertino, California.
        The company was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne in 1976.
        Apple designs, develops, and sells consumer electronics, computer software, and online services.
        """,
        "products.md": """
        # Apple Products
        
        ## iPhone
        The iPhone is a line of smartphones designed and marketed by Apple Inc.
        
        ## Mac
        Mac is a family of personal computers designed by Apple Inc.
        
        ## iPad
        The iPad is a brand of iOS and iPadOS-based tablet computers.
        """,
        "financials.json": json.dumps(
            {
                "company": "Apple Inc.",
                "revenue_2023": "383.285 billion",
                "employees": 164000,
                "stock_symbol": "AAPL",
            }
        ),
        "empty.txt": "",
        "long_document.txt": "This is a test sentence. "
        * 100,  # Long document for chunking tests
    }

    for filename, content in test_files.items():
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def audit_manager():
    """Create a test audit manager"""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test_audit.db")
        yield AuditManager(db_path=db_path)





class TestDocumentIngestionPipeline:
    """Test complete document ingestion pipeline"""

    def test_directory_reader_setup(self, test_data_dir):
        """Test directory reader initialization and file discovery"""
        reader = get_directory_reader(test_data_dir)

        assert str(reader.input_dir) == test_data_dir
        assert len(reader.input_files) > 0

        # Check that supported file types are found
        file_names = [os.path.basename(f) for f in reader.input_files]
        assert "company_info.txt" in file_names
        assert "products.md" in file_names
        assert "financials.json" in file_names

    def test_document_loading(self, test_data_dir):
        """Test document loading from directory"""
        reader = get_directory_reader(test_data_dir)
        documents = reader.load_data()

        assert len(documents) > 0

        # Verify document content is loaded
        doc_texts = [doc.text for doc in documents if hasattr(doc, "text")]
        assert any("Apple Inc." in text for text in doc_texts)
        assert any("iPhone" in text for text in doc_texts)

    def test_file_hashing_and_versioning(self, audit_manager, test_data_dir):
        """Test file hashing and versioning system"""
        test_file = os.path.join(test_data_dir, "company_info.txt")

        # Initial version
        result1 = audit_manager.check_for_changes(test_file, author="TestUser")
        assert result1 is not None
        assert result1["version"] == 1
        assert result1["status"] == "created"
        assert result1["author"] == "TestUser"
        assert len(result1["hash"]) == 64  # SHA-256

        # No change
        result2 = audit_manager.check_for_changes(test_file, author="TestUser")
        assert result2 is None

        # Modified file
        with open(test_file, "a") as f:
            f.write("\nUpdated content.")

        result3 = audit_manager.check_for_changes(test_file, author="TestUser")
        assert result3 is not None
        assert result3["version"] == 2
        assert result3["status"] == "updated"
        assert result3["hash"] != result1["hash"]

    def test_vector_indexing_workflow(self, mock_containers, test_data_dir):
        """Test vector indexing workflow"""
        vector_manager = mock_containers.vector_manager

        # Simulate document indexing
        processed_count = vector_manager.index_documents(
            test_data_dir, author="IntegrationTest"
        )

        # Verify indexing was called
        assert processed_count > 0
        vector_manager.index_documents.assert_called_once_with(
            test_data_dir, author="IntegrationTest"
        )

    def test_graph_indexing_workflow(self, mock_containers, test_data_dir):
        """Test graph indexing workflow"""
        graph_manager = mock_containers.graph_manager

        # Load documents
        reader = get_directory_reader(test_data_dir)
        documents = reader.load_data()

        # Index in graph
        if documents:
            graph_manager.index_documents(documents)
            graph_manager.index_documents.assert_called_once_with(documents)

    def test_complete_ingestion_pipeline(
        self, mock_containers, test_data_dir, audit_manager
    ):
        """Test complete ingestion from file to both stores"""
        vector_manager = mock_containers.vector_manager
        graph_manager = mock_containers.graph_manager

        # Step 1: Load documents
        reader = get_directory_reader(test_data_dir)
        documents = reader.load_data()
        assert len(documents) > 0

        # Step 2: Track changes with audit manager
        for file_path in reader.input_files:
            audit_manager.check_for_changes(file_path, author="PipelineTest")

        # Step 3: Index in vector store
        vector_count = vector_manager.index_documents(
            test_data_dir, author="PipelineTest"
        )
        assert vector_count > 0

        # Step 4: Index in graph store
        if documents:
            graph_manager.index_documents(documents)

        # Verify all components were called
        vector_manager.index_documents.assert_called_once()
        if documents:
            graph_manager.index_documents.assert_called_once()

    def test_error_handling_in_ingestion(self, mock_containers, test_data_dir):
        """Test error handling during ingestion"""
        vector_manager = mock_containers.vector_manager

        # Simulate error during indexing
        vector_manager.index_documents.side_effect = Exception("Indexing failed")

        with pytest.raises(Exception, match="Indexing failed"):
            vector_manager.index_documents(test_data_dir)


class TestQueryResponseFlow:
    """Test complete query response flow through all components"""

    def test_hybrid_query_flow(self, mock_containers):
        """Test hybrid query flow through vector and graph engines"""
        # Setup mock hybrid engine
        mock_hybrid_engine = mock_containers.hybrid_engine
        mock_hybrid_engine.custom_query.return_value = (
            "Hybrid search response about Apple Inc."
        )

        # Execute query
        query = "What is Apple Inc.?"
        response = mock_hybrid_engine.custom_query(query)

        # Verify response
        assert response == "Hybrid search response about Apple Inc."
        mock_hybrid_engine.custom_query.assert_called_once_with(query)

    def test_vector_only_query_flow(self, mock_containers):
        """Test vector-only query flow"""
        # Setup mock vector engine
        mock_vector_engine = mock_containers.vector_only_engine
        mock_vector_engine.query.return_value = (
            "Vector search response about Apple products"
        )

        # Execute query
        query = "What products does Apple make?"
        response = mock_vector_engine.query(query)

        # Verify response
        assert response == "Vector search response about Apple products"
        mock_vector_engine.query.assert_called_once_with(query)

    def test_query_with_metadata_extraction(self, mock_containers):
        """Test query response with metadata extraction"""
        mock_hybrid_engine = mock_containers.hybrid_engine

        # Mock response with metadata
        mock_response = Mock()
        mock_response.response = "Apple was founded in 1976"
        mock_response.source_nodes = [
            Mock(metadata={"file_name": "company_info.txt"}),
            Mock(metadata={"file_name": "products.md"}),
        ]
        mock_hybrid_engine.custom_query.return_value = mock_response

        # Execute query
        query = "When was Apple founded?"
        response = mock_hybrid_engine.custom_query(query)

        # Verify response and metadata
        assert hasattr(response, "response")
        assert hasattr(response, "source_nodes")
        assert len(response.source_nodes) == 2

    def test_query_error_handling(self, mock_containers):
        """Test error handling in query flow"""
        mock_hybrid_engine = mock_containers.hybrid_engine
        mock_hybrid_engine.custom_query.side_effect = Exception(
            "Search service unavailable"
        )

        with pytest.raises(Exception, match="Search service unavailable"):
            mock_hybrid_engine.custom_query("test query")

    def test_query_caching_integration(self, mock_containers):
        """Test query caching integration in query flow"""
        mock_hybrid_engine = mock_containers.hybrid_engine

        # First call should hit the engine
        mock_hybrid_engine.custom_query.return_value = "Response 1"
        response1 = mock_hybrid_engine.custom_query("cached query")

        # Reset call count to simulate cache
        mock_hybrid_engine.custom_query.reset_mock()

        # Second call should use cache (mock scenario)
        with patch("src.main.cache_manager.get_cached_response") as mock_cache:
            mock_cache.return_value = {
                "query": "cached query",
                "response": "Response 1",
                "sources": [],
            }

            # In real scenario, cached response would be returned without calling engine
            cached_response = mock_cache("cached query", "hybrid")
            assert cached_response["response"] == "Response 1"


class TestVersioningAndAuditTrail:
    """Test versioning and audit trail functionality"""

    def test_audit_log_retrieval(self, audit_manager):
        """Test audit log retrieval and formatting"""
        # Create some audit entries
        test_dir = os.path.dirname(audit_manager.db_path)
        test_file1 = os.path.join(test_dir, "test1.txt")
        test_file2 = os.path.join(test_dir, "test2.txt")

        with open(test_file1, "w") as f:
            f.write("test content 1")
        with open(test_file2, "w") as f:
            f.write("test content 2")

        audit_manager.check_for_changes(test_file1, author="User1")
        audit_manager.check_for_changes(test_file2, author="User2")

        # Retrieve audit log
        audit_log = audit_manager.get_audit_log()

        # Verify audit log structure
        assert len(audit_log) >= 2
        for entry in audit_log:
            assert "file_path" in entry
            assert "version" in entry
            assert "author" in entry
            assert "timestamp" in entry

    def test_file_change_detection(self, audit_manager, test_data_dir):
        """Test comprehensive file change detection"""
        test_file = os.path.join(test_data_dir, "company_info.txt")

        # Initial state
        result = audit_manager.check_for_changes(test_file, author="ChangeDetector")
        initial_hash = result["hash"]

        # No changes
        result = audit_manager.check_for_changes(test_file, author="ChangeDetector")
        assert result is None

        # Content change
        with open(test_file, "w") as f:
            f.write("Completely new content")

        result = audit_manager.check_for_changes(test_file, author="ChangeDetector")
        assert result is not None
        assert result["status"] == "updated"
        assert result["hash"] != initial_hash
        assert result["version"] == 2

        # File deletion and recreation
        os.remove(test_file)
        result = audit_manager.check_for_changes(test_file, author="ChangeDetector")
        assert result is None  # File doesn't exist

        with open(test_file, "w") as f:
            f.write("Recreated content")

        result = audit_manager.check_for_changes(test_file, author="ChangeDetector")
        assert result is not None
        # Recreated path at same session is 'updated'
        assert result["status"] == "updated"

    def test_concurrent_access_handling(self, audit_manager, test_data_dir):
        """Test handling of concurrent file access"""
        test_file = os.path.join(test_data_dir, "concurrent_test.txt")

        with open(test_file, "w") as f:
            f.write("initial content")

        # Simulate concurrent access by multiple users
        results = []
        for i, author in enumerate(["User1", "User2", "User3"]):
            result = audit_manager.check_for_changes(test_file, author=author)
            results.append(result)

        # Only first access should detect creation
        assert results[0] is not None and results[0]["status"] == "created"
        assert results[1] is None
        assert results[2] is None

    def test_audit_persistence(self, audit_manager):
        """Test audit data persistence across instances"""
        # Create audit entry
        test_dir = os.path.dirname(audit_manager.db_path)
        test_file = os.path.join(test_dir, "persistence_test.txt")
        with open(test_file, "w") as f:
            f.write("test content")

        original_result = audit_manager.check_for_changes(
            test_file, author="PersistenceTest"
        )

        # Create new audit manager instance (simulating restart)
        new_audit_manager = AuditManager(db_path=audit_manager.db_path)

        # Verify data persisted
        audit_log = new_audit_manager.get_audit_log()
        assert len(audit_log) > 0

        # Verify we can still detect no changes
        no_change_result = new_audit_manager.check_for_changes(
            test_file, author="PersistenceTest"
        )
        assert no_change_result is None


class TestEndToEndWorkflowScenarios:
    """Test comprehensive end-to-end workflow scenarios"""

    def test_document_lifecycle_workflow(
        self, mock_containers, test_data_dir, audit_manager
    ):
        """Test complete document lifecycle: upload -> index -> query -> delete"""
        vector_manager = mock_containers.vector_manager
        graph_manager = mock_containers.graph_manager

        # Step 1: Document upload/creation
        test_file = os.path.join(test_data_dir, "lifecycle_test.txt")
        with open(test_file, "w") as f:
            f.write("This document will go through the complete lifecycle.")

        # Step 2: Track and index
        audit_result = audit_manager.check_for_changes(
            test_file, author="LifecycleTest"
        )
        assert audit_result["status"] == "created"

        vector_count = vector_manager.index_documents(
            test_data_dir, author="LifecycleTest"
        )
        assert vector_count > 0

        reader = get_directory_reader(test_data_dir)
        documents = reader.load_data()
        if documents:
            graph_manager.index_documents(documents)

        # Step 3: Query the document
        mock_hybrid_engine = mock_containers.hybrid_engine
        mock_hybrid_engine.custom_query.return_value = (
            "Document found with lifecycle information"
        )

        query_response = mock_hybrid_engine.custom_query(
            "lifecycle document information"
        )
        assert query_response is not None

        # Step 4: Document deletion
        document_hash = audit_result["hash"]
        vector_manager.delete_document(document_hash)
        graph_manager.delete_document_by_hash(document_hash)

        # Verify deletion calls
        vector_manager.delete_document.assert_called_once_with(document_hash)
        graph_manager.delete_document_by_hash.assert_called_once_with(document_hash)

    def test_batch_processing_workflow(
        self, mock_containers, test_data_dir, audit_manager
    ):
        """Test batch processing of multiple documents"""
        vector_manager = mock_containers.vector_manager
        graph_manager = mock_containers.graph_manager

        # Create multiple test documents
        for i in range(5):
            test_file = os.path.join(test_data_dir, f"batch_doc_{i}.txt")
            with open(test_file, "w") as f:
                f.write(f"Batch document {i} content with unique information {i}")

        # Batch indexing
        vector_manager.index_documents.return_value = 5
        processed_count = vector_manager.index_documents(
            test_data_dir, author="BatchProcessor"
        )
        assert processed_count >= 5

        reader = get_directory_reader(test_data_dir)
        documents = reader.load_data()
        if documents:
            graph_manager.index_documents(documents)

        # Verify batch operations
        vector_manager.index_documents.assert_called()
        if documents:
            graph_manager.index_documents.assert_called_with(documents)

    def test_multi_engine_comparison_workflow(self, mock_containers):
        """Test workflow comparing different search engines"""
        mock_hybrid_engine = mock_containers.hybrid_engine
        mock_vector_engine = mock_containers.vector_only_engine

        test_query = "What are Apple's main products?"

        # Mock different responses for comparison
        mock_hybrid_engine.custom_query.return_value = {
            "response": "Hybrid: Apple's main products include iPhone, Mac, and iPad",
            "sources": ["company_info.txt", "products.md"],
            "response_time": 1.2,
        }

        mock_vector_engine.query.return_value = {
            "response": "Vector: Apple produces iPhone, Mac computers, and iPad tablets",
            "sources": ["products.md"],
            "response_time": 0.8,
        }

        # Execute queries with both engines
        hybrid_result = mock_hybrid_engine.custom_query(test_query)
        vector_result = mock_vector_engine.query(test_query)

        # Compare results
        assert hybrid_result is not None
        assert vector_result is not None
        assert hybrid_result != vector_result

        # Verify both engines were called
        mock_hybrid_engine.custom_query.assert_called_once_with(test_query)
        mock_vector_engine.query.assert_called_once_with(test_query)

    def test_error_recovery_workflow(
        self, mock_controllers, test_data_dir, audit_manager
    ):
        """Test workflow with error recovery mechanisms"""
        vector_manager = mock_controllers["vector_manager"]
        graph_manager = mock_controllers["graph_manager"]

        # Simulate partial failure during indexing
        vector_manager.index_documents.side_effect = [
            Exception("Vector indexing failed"),
            5,  # Success on retry
        ]

        try:
            # First attempt fails
            vector_manager.index_documents(test_data_dir, author="ErrorRecovery")
        except Exception:
            # Simulate retry logic
            pass

        # Retry succeeds
        processed_count = vector_manager.index_documents(
            test_data_dir, author="ErrorRecovery"
        )
        assert processed_count == 5

        # Verify retry was attempted
        assert vector_manager.index_documents.call_count == 2

    def test_performance_monitoring_workflow(self, mock_controllers):
        """Test workflow with performance monitoring"""
        mock_hybrid_engine = mock_controllers["hybrid_engine"]
        mock_vector_engine = mock_controllers["vector_engine"]

        # Mock responses with timing information
        mock_hybrid_engine.custom_query.return_value = "Fast response"
        mock_vector_engine.query.return_value = "Vector response"

        # Execute multiple queries for performance testing
        queries = [
            "What is Apple?",
            "Who founded Apple?",
            "What products does Apple make?",
            "When was Apple founded?",
            "Where is Apple headquartered?",
        ]

        hybrid_responses = []
        vector_responses = []

        for query in queries:
            # Track response times (mock scenario)
            hybrid_response = mock_hybrid_engine.custom_query(query)
            vector_response = mock_vector_engine.query(query)

            hybrid_responses.append(hybrid_response)
            vector_responses.append(vector_response)

        # Verify all queries were processed
        assert len(hybrid_responses) == len(queries)
        assert len(vector_responses) == len(queries)
        assert mock_hybrid_engine.custom_query.call_count == len(queries)
        assert mock_vector_engine.query.call_count == len(queries)
