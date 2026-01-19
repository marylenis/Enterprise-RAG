# Integration Test Documentation

## Overview

This directory contains comprehensive integration tests for the Enterprise RAG system. The integration tests verify that all components work together correctly and that the system functions as expected in realistic scenarios.

## Test Categories

### 1. API Integration Tests (`test_api_integration.py`)
Tests the FastAPI endpoints and request/response handling.

**Coverage:**
- Health check endpoint
- Query endpoints (hybrid and vector-only)
- File upload and ingestion
- Document deletion
- Audit trail functionality
- Statistics endpoints
- Cache management
- Error handling and edge cases

### 2. Database Integration Tests (`test_database_integration.py`)
Tests integration with the three database systems.

**Coverage:**
- Redis caching functionality
- Qdrant vector database operations
- FalkorDB graph database operations
- Cross-database data flow
- Database error handling
- Connection management

### 3. End-to-End Workflow Tests (`test_e2e_workflows.py`)
Tests complete user workflows through the system.

**Coverage:**
- Document ingestion pipeline
- Query response flow
- Versioning and audit trail
- Batch processing
- Multi-engine comparison
- Error recovery
- Performance monitoring

### 4. Docker Integration Tests (`test_docker_integration.py`)
Tests Docker container setup and communication.

**Coverage:**
- Container connectivity
- Health checks
- Service dependencies
- Networking configuration
- Resource management
- Log monitoring

### 5. Frontend-Backend Integration Tests (`test_frontend_backend.py`)
Tests frontend API integration and data flow.

**Coverage:**
- Frontend API calls
- Response format validation
- Error handling
- Data flow patterns
- Performance optimizations
- User experience scenarios

## Running Tests

### Prerequisites

1. **Python Environment:**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-mock pytest-xdist pytest-cov
   ```

2. **Docker Environment:**
   ```bash
   # Install Docker and Docker Compose
   docker --version
   docker-compose --version
   ```

3. **Database Services:**
   ```bash
   # Start required services
   docker-compose up -d redis qdrant falkordb
   ```

### Running Individual Test Files

```bash
# Run API integration tests
pytest tests/integration/test_api_integration.py -v

# Run database integration tests
pytest tests/integration/test_database_integration.py -v

# Run end-to-end workflow tests
pytest tests/integration/test_e2e_workflows.py -v

# Run Docker integration tests
pytest tests/integration/test_docker_integration.py -v

# Run frontend-backend integration tests
pytest tests/integration/test_frontend_backend.py -v
```

### Using the Test Runner

The `run_integration_tests.py` script provides a convenient way to run tests with proper setup:

```bash
# Run all integration tests
python tests/run_integration_tests.py

# Run specific test types
python tests/run_integration_tests.py --type api
python tests/run_integration_tests.py --type database
python tests/run_integration_tests.py --type e2e
python tests/run_integration_tests.py --type docker
python tests/run_integration_tests.py --type frontend

# Run with coverage
python tests/run_integration_tests.py --coverage

# Run tests in parallel
python tests/run_integration_tests.py --parallel

# Run without starting services (use existing ones)
python tests/run_integration_tests.py --no-services

# Quiet mode
python tests/run_integration_tests.py --quiet

# Cleanup only
python tests/run_integration_tests.py --cleanup-only
```

### Test Categories and Markers

The tests use pytest markers for categorization:

```bash
# Run only integration tests
pytest tests/integration/ -m integration

# Skip slow tests
pytest tests/integration/ -m "not slow"

# Skip Docker-dependent tests
pytest tests/integration/ -m "not docker"

# Skip database-dependent tests
pytest tests/integration/ -m "not database"
```

## Configuration

### Environment Variables

Integration tests use the following environment variables:

```bash
# Database Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
QDRANT_HOST=localhost
QDRANT_PORT=6333
FALKORDB_HOST=localhost
FALKORDB_PORT=6380

# API Configuration
OPENAI_API_KEY=your-api-key-here
PYTHONPATH=/path/to/project

# Test Configuration
INTEGRATION_TEST=true
TESTING=true
QDRANT_COLLECTION=test_enterprise_docs
FALKORDB_GRAPH=test_enterprise_knowledge
```

### Test Data

Test data files are located in `tests/test_data/`:

- `sample_document.txt` - Sample text document
- `api_documentation.md` - API documentation
- `.env.test` - Test environment configuration

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
      
      qdrant:
        image: qdrant/qdrant:latest
        ports:
          - 6333:6333
      
      falkordb:
        image: falkordb/falkordb:latest
        ports:
          - 6380:6379
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-mock pytest-cov
    
    - name: Run integration tests
      run: |
        python tests/run_integration_tests.py --coverage
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
      with:
        file: ./htmlcov/index.html
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    
    stages {
        stage('Setup') {
            steps {
                sh 'docker-compose up -d redis qdrant falkordb'
            }
        }
        
        stage('Integration Tests') {
            steps {
                sh 'python tests/run_integration_tests.py --coverage'
            }
            post {
                always {
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Integration Test Coverage'
                    ])
                }
            }
        }
        
        stage('Cleanup') {
            steps {
                sh 'docker-compose down'
            }
        }
    }
}
```

## Test Structure

### Fixtures

The tests use shared fixtures defined in `conftest.py`:

- `setup_test_environment` - Global test environment setup
- `temp_directory` - Temporary directory for test files
- `mock_openai_client` - Mock OpenAI client
- `sample_documents` - Sample document data
- `sample_queries` - Sample query data
- `integration_helper` - Utility functions for integration tests

### Mock Strategy

Integration tests use a layered mocking approach:

1. **External Services Mocked:** OpenAI API, external HTTP calls
2. **Internal Services Real:** Database connections, internal API calls
3. **Component Mocking:** Individual components can be mocked for isolation

### Error Scenarios

The tests cover comprehensive error scenarios:

- Network failures
- Database connection errors
- Invalid input data
- Service unavailability
- Resource exhaustion
- Authentication/authorization errors

## Performance Testing

### Response Time Testing

```python
def test_query_response_time(performance_tracker):
    performance_tracker.start()
    
    # Execute query
    response = make_query("test query")
    
    performance_tracker.stop()
    
    # Assert response time is acceptable
    assert performance_tracker.duration < 5.0  # 5 seconds
```

### Load Testing

```python
def test_concurrent_queries():
    import concurrent.futures
    
    def make_query():
        return requests.post("/query", json={"query": "test"})
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_query) for _ in range(100)]
        results = [f.result() for f in futures]
    
    # Assert all queries succeeded
    assert all(r.status_code == 200 for r in results)
```

## Troubleshooting

### Common Issues

1. **Docker Service Not Starting**
   ```bash
   # Check Docker status
   docker ps
   docker-compose ps
   
   # Check logs
   docker-compose logs redis
   docker-compose logs qdrant
   docker-compose logs falkordb
   ```

2. **Port Conflicts**
   ```bash
   # Check what's using ports
   netstat -tulpn | grep :6379
   netstat -tulpn | grep :6333
   netstat -tulpn | grep :6380
   ```

3. **Import Errors**
   ```bash
   # Check Python path
   echo $PYTHONPATH
   python -c "import sys; print(sys.path)"
   
   # Install missing packages
   pip install -r requirements.txt
   ```

4. **Test Timeout**
   ```bash
   # Increase timeout in pytest.ini
   # or run with longer timeout
   pytest --timeout=600
   ```

### Debug Mode

Enable debug output:

```bash
# Verbose pytest output
pytest tests/integration/ -v -s

# Enable debug logging
pytest tests/integration/ --log-cli-level=DEBUG

# Run single test for debugging
pytest tests/integration/test_api_integration.py::TestQueryEndpoints::test_query_hybrid_engine -v -s
```

## Best Practices

1. **Test Isolation:** Each test should be independent and not rely on state from other tests
2. **Cleanup:** Always clean up test data and state after tests run
3. **Mock External Dependencies:** Avoid calling external services in tests
4. **Use Fixtures:** Leverage pytest fixtures for common setup/teardown
5. **Assert Responsibly:** Focus on testing behavior, not implementation details
6. **Performance Testing:** Include performance tests for critical paths
7. **Error Testing:** Test both success and failure scenarios
8. **Documentation:** Document test scenarios and expected behaviors

## Contributing

When adding new integration tests:

1. Follow the existing test structure and naming conventions
2. Use appropriate markers for test categorization
3. Include both positive and negative test cases
4. Document the test purpose and expected behavior
5. Ensure tests are independent and can run in parallel
6. Update this documentation if adding new test categories