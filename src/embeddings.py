from llama_index.core.node_parser import TokenTextSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings
import os
from dotenv import load_dotenv

load_dotenv()

def configure_embeddings_and_chunking():
    """
    Configures the global embedding model and node parser (chunking strategy).
    """
    # 1. Configure the Embedding Model
    # Using text-embedding-3-small as suggested for cost/efficiency
    embed_model = OpenAIEmbedding(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # 2. Configure the Node Parser (Chunking)
    # Using 300-500 tokens as defined in the plan with 10% overlap (50 tokens)
    node_parser = TokenTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separator=" "
    )
    
    # Set global settings for LlamaIndex
    Settings.embed_model = embed_model
    Settings.node_parser = node_parser
    
    return embed_model, node_parser

if __name__ == "__main__":
    # Test configuration
    try:
        embed, parser = configure_embeddings_and_chunking()
        print("Embeddings y Chunking configurados exitosamente.")
        print(f"Modelo: {embed.model_name}")
        print(f"Chunk Size: {parser.chunk_size}")
    except Exception as e:
        print(f"Error al configurar: {e}")
