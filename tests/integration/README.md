Enterprise RAG System Integration Tests

This directory contains comprehensive integration tests for the Enterprise RAG system.

## Test Categories

1. **API Integration Tests** (`test_api_integration.py`)
   - FastAPI endpoint testing
   - File upload and ingestion flow
   - Query endpoints with different engine types
   - Error handling and edge cases

2. **Database Integration Tests** (`test_database_integration.py`)
   - Qdrant vector database integration
   - Redis caching functionality
   - FalkorDB graph database operations

3. **End-to-End Workflow Tests** (`test_e2e_workflows.py`)
   - Complete document ingestion pipeline
   - Query response flow through all components
   - Versioning and audit trail functionality

4. **Docker Integration Tests** (`test_docker_integration.py`)
   - Container communication
   - Health checks
   - Service dependencies

5. **Frontend-Backend Integration Tests** (`test_frontend_backend.py`)
   - Frontend API calls
   - Response format validation

## Test Data

Test data files are stored in the `test_data/` directory:
- Sample PDF documents
- Sample text files
- Sample markdown files
- Configuration files for testing

## Running Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific test category
pytest tests/integration/test_api_integration.py -v

# Run with coverage
pytest tests/integration/ --cov=src --cov-report=html

# Run tests in parallel
pytest tests/integration/ -n auto
```

## Requirements

Integration tests require:
- Docker and Docker Compose
- Test databases running (Redis, Qdrant, FalkorDB)
- Environment variables configured
- Test data files available

## CI/CD Integration

These tests are designed to run in CI/CD pipelines:
- Independent test execution
- Proper cleanup and teardown
- Mocked external dependencies where appropriate
- Parallel execution support