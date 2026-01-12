import os
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from dotenv import load_dotenv
from src.versioning import AuditManager
from src.loader import get_directory_reader

load_dotenv()

class VectorIndexManager:
    def __init__(self, collection_name: str = "enterprise_docs"):
        self.collection_name = collection_name
        self.client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", 6333))
        )
        self.audit_manager = AuditManager()
        self.vector_store = QdrantVectorStore(
            client=self.client, 
            collection_name=self.collection_name
        )
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

    def index_documents(self, data_path: str, author: str = "System"):
        """
        Scans the directory, checks for changes, and indexes new versions in Qdrant.
        """
        reader = get_directory_reader(data_path)
        documents = reader.load_data()
        
        # Group by file path to handle versioning per file
        files_to_process = set([doc.metadata.get("file_path") for doc in documents])
        
        indexed_count = 0
        for file_path in files_to_process:
            if not file_path: continue
            
            audit_info = self.audit_manager.check_for_changes(file_path, author)
            
            if audit_info:
                print(f"Detectado cambio en {file_path}. Indexando versión {audit_info['version']}...")
                
                # Filter documents that belong to this file
                file_docs = [doc for doc in documents if doc.metadata.get("file_path") == file_path]
                
                # Enrich metadata for each chunk/node
                for doc in file_docs:
                    doc.metadata.update({
                        "version_id": audit_info["version"],
                        "author": audit_info["author"],
                        "updated_at": audit_info.get("timestamp", ""),
                        "is_active": True,
                        "file_hash": audit_info["hash"]
                    })
                
                # Index the new version
                # Note: LlamaIndex handle the chunking automatically if we use VectorStoreIndex.from_documents
                # but we want to mark OLD versions as inactive in Qdrant before or after.
                self._deactivate_old_versions(file_path)
                
                VectorStoreIndex.from_documents(
                    file_docs,
                    storage_context=self.storage_context,
                    show_progress=True
                )
                indexed_count += 1
            else:
                print(f"Sin cambios para {file_path}. Saltando...")

        return indexed_count

    def _deactivate_old_versions(self, file_path: str):
        """
        Update is_active metadata for previous versions of the file in Qdrant.
        """
        self.client.set_payload(
            collection_name=self.collection_name,
            payload={"is_active": False},
            points_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="file_path",
                        match=models.MatchValue(value=file_path)
                    ),
                    models.FieldCondition(
                        key="is_active",
                        match=models.MatchValue(value=True)
                    )
                ]
            )
        )

if __name__ == "__main__":
    # Test vector index manager
    try:
        data_dir = os.path.join(os.getcwd(), "data")
        manager = VectorIndexManager()
        count = manager.index_documents(data_dir)
        print(f"Proceso finalizado. Archivos nuevos/actualizados: {count}")
    except Exception as e:
        print(f"Error en el vector store: {e}")
