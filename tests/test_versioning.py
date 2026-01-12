import os
import pytest
from src.versioning import AuditManager

@pytest.fixture
def audit_manager(tmp_path):
    db_file = tmp_path / "test_audit.db"
    return AuditManager(db_path=str(db_file))

def test_init_db(audit_manager):
    assert os.path.exists(audit_manager.db_path)

def test_get_file_hash(audit_manager, tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")
    
    hash1 = audit_manager.get_file_hash(str(test_file))
    assert len(hash1) == 64 # SHA-256 length
    
    test_file.write_text("hello world modified")
    hash2 = audit_manager.get_file_hash(str(test_file))
    assert hash1 != hash2

def test_check_for_changes_new_file(audit_manager, tmp_path):
    test_file = tmp_path / "new.txt"
    test_file.write_text("initial content")
    
    result = audit_manager.check_for_changes(str(test_file), author="TestAuthor")
    assert result is not None
    assert result["version"] == 1
    assert result["status"] == "created"
    assert result["author"] == "TestAuthor"

def test_check_for_changes_modified_file(audit_manager, tmp_path):
    test_file = tmp_path / "mod.txt"
    test_file.write_text("v1")
    
    # First check (create)
    audit_manager.check_for_changes(str(test_file))
    
    # Modify
    test_file.write_text("v2")
    result = audit_manager.check_for_changes(str(test_file))
    
    assert result is not None
    assert result["version"] == 2
    assert result["status"] == "updated"

def test_check_for_changes_no_change(audit_manager, tmp_path):
    test_file = tmp_path / "same.txt"
    test_file.write_text("permanent content")
    
    audit_manager.check_for_changes(str(test_file))
    result = audit_manager.check_for_changes(str(test_file))
    
    assert result is None
