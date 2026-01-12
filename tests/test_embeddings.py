import pytest
from src.embeddings import configure_embeddings_and_chunking
from llama_index.core import Settings

def test_configure_embeddings_and_chunking(mocker):
    # Mock environment variables
    mocker.patch("os.getenv", return_value="fake_api_key")
    
    embed, parser = configure_embeddings_and_chunking()
    
    assert embed.model_name == "text-embedding-3-small"
    assert parser.chunk_size == 500
    assert parser.chunk_overlap == 50
    
    # Check if global settings were updated
    assert Settings.embed_model == embed
    assert Settings.node_parser == parser
