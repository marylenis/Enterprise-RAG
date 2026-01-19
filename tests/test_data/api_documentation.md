# API Documentation

## Health Check

- **Endpoint**: `/health`
- **Method**: GET
- **Description**: Check if the API is running
- **Response**: `{"status": "healthy", "service": "Enterprise RAG"}`

## Query Endpoints

### Query System
- **Endpoint**: `/query`
- **Method**: POST
- **Request Body**:
```json
{
  "query": "What are the main components?",
  "engine_type": "hybrid"  // or "vector"
}
```
- **Response**:
```json
{
  "query": "What are the main components?",
  "response": "The main components are...",
  "sources": ["document1.txt", "document2.txt"]
}
```

## Document Management

### Upload File
- **Endpoint**: `/upload`
- **Method**: POST
- **Content-Type**: multipart/form-data
- **Form Fields**:
  - `file`: File to upload
  - `author`: Author name (optional)

### Ingest Data
- **Endpoint**: `/ingest`
- **Method**: POST
- **Request Body**:
```json
{
  "data_path": "/path/to/data",
  "author": "System"
}
```

### Delete Document
- **Endpoint**: `/delete-document`
- **Method**: DELETE
- **Request Body**:
```json
{
  "file_path": "/path/to/file",
  "hash": "document_hash"
}
```

## Audit and Monitoring

### Get Audit Trail
- **Endpoint**: `/audit`
- **Method**: GET
- **Response**: Array of audit log entries

### Get Cache Stats
- **Endpoint**: `/stats/cache`
- **Method**: GET

### Get Cost Stats
- **Endpoint**: `/stats/costs`
- **Method**: GET

### Get Usage Stats
- **Endpoint**: `/stats/usage`
- **Method**: GET

## Evaluation

### Run Evaluation
- **Endpoint**: `/evaluate`
- **Method**: POST

### Compare Engines
- **Endpoint**: `/evaluate/compare`
- **Method**: GET

## Cache Management

### Clear Cache
- **Endpoint**: `/cache`
- **Method**: DELETE
- **Query Parameters**:
  - `pattern`: Pattern to match cache entries (optional)