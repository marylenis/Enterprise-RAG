from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File
import shutil
import os
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from fastapi import Query
from pydantic import Field
from src.containers import Container
from src.hybrid_engine import HybridQueryEngine
from src.vector_store import VectorIndexManager
from src.graph_manager import GraphManager
from src.embeddings import configure_embeddings_and_chunking
from src.loader import get_directory_reader
from src.cache_manager import CacheManager
from src.cost_control import CostOptimizer, CostControlMiddleware
from src.evaluation import RAGEvaluator
from dotenv import load_dotenv

load_dotenv()

# Initialize Global Settings
configure_embeddings_and_chunking()

app = FastAPI(title="Enterprise RAG API", version="1.0.0")

# Initialize cost control and caching
cost_optimizer = CostOptimizer()
cache_manager = CacheManager()

# Add cost control middleware
app.add_middleware(CostControlMiddleware, cost_optimizer=cost_optimizer)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    allow_credentials=True,
)


# Request/Response Models
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Query cannot be empty")
    engine_type: str = "hybrid"  # hybrid, vector


class QueryResponse(BaseModel):
    query: str
    response: str
    sources: Optional[List[str]] = []


class DeleteRequest(BaseModel):
    file_path: str
    hash: str


class IngestRequest(BaseModel):
    data_path: Optional[str] = None
    author: str = "System"


class IngestResponse(BaseModel):
    status: str
    files_processed: int


# Container Setup
container = Container()


# Dependency override helpers
def get_hybrid_engine():
    return container.hybrid_engine()


def get_vector_only_engine():
    return container.vector_only_engine()


def get_vector_manager():
    return container.vector_manager()


def get_graph_manager():
    return container.graph_manager()


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Enterprise RAG"}


@app.post("/query", response_model=QueryResponse)
def query_system(
    request: QueryRequest,
    http_request: Request,
    hybrid_engine: HybridQueryEngine = Depends(get_hybrid_engine),
    vector_only_engine=Depends(get_vector_only_engine),
):
    """
    Primary RAG query endpoint that supports multiple engine types.
    """
    try:
        # Extract client info
        client_id = http_request.client.host
        tier = http_request.headers.get("X-API-Tier", "default")

        # Check cache first
        cached_response = cache_manager.get_cached_response(
            request.query, request.engine_type
        )
        if cached_response:
            # Track cache hit
            cost_optimizer.track_request_cost(client_id, 0, 0, cache_hit=True)
            return QueryResponse(**cached_response)

        # Estimate input tokens
        input_tokens = cost_optimizer.estimate_tokens(request.query)

        # Check token limits
        token_check = cost_optimizer.token_manager.track_tokens(
            client_id, input_tokens, tier
        )
        if not token_check["allowed"]:
            raise HTTPException(status_code=429, detail=token_check["reason"])

        # Process query
        if request.engine_type == "hybrid" or request.engine_type == "graph":
            response = hybrid_engine.custom_query(request.query)
        else:
            response = vector_only_engine.query(request.query)

        # Estimate output tokens
        output_tokens = cost_optimizer.estimate_tokens(str(response))

        # Track costs and tokens
        cost_optimizer.track_request_cost(client_id, input_tokens, output_tokens)
        cost_optimizer.token_manager.track_tokens(client_id, output_tokens, tier)

        # Prepare response
        query_response = QueryResponse(
            query=request.query,
            response=str(response),
            sources=[],  # TODO: Extract actual sources from response metadata
        )

        # Cache the response
        cache_manager.cache_response(
            request.query, query_response.model_dump(), request.engine_type
        )

        return query_response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/delete-document")
async def delete_document(
    file_path: str = Query(...),
    hash: str = Query(...),
    vector_manager: VectorIndexManager = Depends(get_vector_manager),
    graph_manager: GraphManager = Depends(get_graph_manager),
):
    """
    Delete a document from both vector store and graph store
    """
    try:
        file_hash = hash

        if not file_path or not file_hash:
            raise HTTPException(
                status_code=400, detail="file_path and hash are required"
            )

        # Delete from vector store
        vector_manager.delete_document(file_hash)

        # Delete from graph store
        graph_manager.delete_document_by_hash(file_hash)

        # Delete physical file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Could not delete physical file {file_path}: {e}")

        return {"status": "success", "message": "Document deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload", response_model=IngestResponse)
async def upload_file(
    file: UploadFile = File(...),
    author: str = "Web User",
    vector_manager: VectorIndexManager = Depends(get_vector_manager),
    graph_manager: GraphManager = Depends(get_graph_manager),
):
    try:
        # Save file to data directory
        data_dir = os.path.join(os.getcwd(), "data")
        os.makedirs(data_dir, exist_ok=True)
        file_path = os.path.join(data_dir, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Trigger ingestion for this specific file
        processed_count = vector_manager.index_documents(
            data_dir,
            author=author,  # Re-scan directory for simplicity, or we could pass specific file if supported
        )

        # Graph Indexing (simplistic - reloads all)
        # For a production system this should be more targeted
        reader = get_directory_reader(data_dir)
        documents = reader.load_data()
        if documents:
            graph_manager.index_documents(documents)

        return IngestResponse(status="success", files_processed=processed_count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest", response_model=IngestResponse)
def ingest_data(
    request: IngestRequest,
    vector_manager: VectorIndexManager = Depends(get_vector_manager),
    graph_manager: GraphManager = Depends(get_graph_manager),
):
    try:
        data_path = request.data_path or os.path.join(os.getcwd(), "data")

        # 1. Index in Vector Store
        processed_count = vector_manager.index_documents(
            data_path, author=request.author
        )

        # 2. Index in Graph Store
        # (We reload documents to process them through the graph extractor)
        reader = get_directory_reader(data_path)
        documents = reader.load_data()
        if documents:
            graph_manager.index_documents(documents)

        return IngestResponse(status="success", files_processed=processed_count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/audit")
def get_audit_trail(vector_manager: VectorIndexManager = Depends(get_vector_manager)):
    # Retrieve audit from SQLite
    try:
        results = vector_manager.audit_manager.get_audit_log()
        # Convert timestamp to string to avoid JSON serialization issues
        for item in results:
            if "timestamp" in item:
                item["timestamp"] = str(item["timestamp"])
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/cache")
def get_cache_stats():
    """Get cache performance statistics"""
    try:
        return cache_manager.get_cache_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/costs")
def get_cost_stats(http_request: Request):
    """Get cost statistics for client or global"""
    try:
        client_id = http_request.client.host
        return cost_optimizer.get_cost_stats(client_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/usage")
def get_usage_stats(http_request: Request):
    """Get usage statistics for client"""
    try:
        client_id = http_request.client.host
        tier = http_request.headers.get("X-API-Tier", "default")

        return {
            "rate_limiting": cost_optimizer.rate_limiter.get_usage_stats(client_id),
            "token_usage": cost_optimizer.token_manager.get_token_stats(client_id),
            "tier": tier,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cache")
def clear_cache(pattern: Optional[str] = None):
    """Clear cache entries"""
    try:
        cleared_count = cache_manager.invalidate_cache(pattern)
        return {"status": "success", "cleared_entries": cleared_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SettingsUpdateRequest(BaseModel):
    category: str
    key: str
    value: Any


class SettingsCategoryUpdateRequest(BaseModel):
    values: Dict[str, Any]


@app.get("/settings")
def get_all_settings():
    """Get all current settings"""
    from src.settings_manager import get_settings_dict

    try:
        return get_settings_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/settings/{category}")
def get_category_settings(category: str):
    """Get settings for a specific category"""
    from src.settings_manager import get_category

    try:
        settings = get_category(category)
        if settings is None:
            raise HTTPException(status_code=404, detail="Category not found")
        return {category: settings}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/settings")
def update_setting(request: SettingsUpdateRequest):
    """Update a specific setting"""
    from src.settings_manager import update_setting as update_setting_func

    try:
        success = update_setting_func(request.category, request.key, request.value)
        if success:
            return {
                "status": "updated",
                "category": request.category,
                "key": request.key,
                "value": request.value,
            }
        raise HTTPException(status_code=400, detail="Failed to update setting")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/settings/{category}")
def update_category_settings(category: str, request: SettingsCategoryUpdateRequest):
    """Update an entire category with new values"""
    from src.settings_manager import update_category as update_category_func

    try:
        success = update_category_func(category, request.values)
        if success:
            return {"status": "updated", "category": category, "values": request.values}
        raise HTTPException(status_code=400, detail="Failed to update category")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/settings/reset")
def reset_settings():
    """Reset all settings to defaults"""
    from src.settings_manager import reset_to_defaults

    try:
        success = reset_to_defaults()
        if success:
            return {
                "status": "reset",
                "message": "All settings have been reset to defaults",
            }
        raise HTTPException(status_code=500, detail="Failed to reset settings")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evaluate")
async def run_evaluation(request: Request = None):
    """Run RAG system quality evaluation"""
    try:
        body = await request.json() if request else {}
        custom_queries = body.get("queries", None)

        evaluator = RAGEvaluator()

        if custom_queries and len(custom_queries) > 0:
            test_queries = custom_queries
        else:
            test_queries = evaluator.generate_test_queries("enterprise")

        results = await evaluator.evaluate_system(test_queries)

        return {
            "status": "success",
            "evaluation_id": results["timestamp"],
            "overall_scores": results["overall_scores"],
            "total_queries": results["total_queries"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/evaluate/compare")
def compare_engines():
    """Compare performance between hybrid and vector-only engines"""
    try:
        evaluator = RAGEvaluator()
        test_queries = evaluator.generate_test_queries("enterprise")
        results = evaluator.compare_engines(test_queries)

        return {"status": "success", "comparison": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
