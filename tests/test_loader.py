import os
import pytest
from src.loader import get_directory_reader

def test_get_directory_reader_config(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "placeholder.md").write_text("dummy content")
    
    reader = get_directory_reader(str(data_dir))
    
    assert reader.input_dir == str(data_dir)
    assert ".pdf" in reader.required_exts
    assert ".md" in reader.required_exts
    assert ".docx" in reader.required_exts
    assert ".xlsx" in reader.required_exts

def test_loader_creates_dir_if_missing(tmp_path):
    missing_dir = tmp_path / "not_here"
    # Note: get_directory_reader creates the dir, but SLR will fail if empty.
    # We create a file to avoid ValueError.
    os.makedirs(str(missing_dir), exist_ok=True)
    (missing_dir / "placeholder.md").write_text("dummy content")
    
    reader = get_directory_reader(str(missing_dir))
    assert os.path.exists(missing_dir)
    assert len(reader.input_files) > 0
