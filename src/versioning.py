import hashlib
import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict


class AuditManager:
    def __init__(self, db_path: str = "config/audit.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the audit database if it doesn't exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    author TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    version_number INTEGER NOT NULL,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            conn.commit()

    def get_file_hash(self, file_path: str) -> str:
        """Generates SHA-256 hash for a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def check_for_changes(
        self, file_path: str, author: str = "System"
    ) -> Optional[Dict]:
        """
        Heuristic to detect changes. Returns audit info if changed or new.
        """
        current_hash = self.get_file_hash(file_path)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Get latest version for this file
            cursor.execute(
                "SELECT file_hash, version_number FROM document_audit WHERE file_path = ? ORDER BY version_number DESC LIMIT 1",
                (file_path,),
            )
            result = cursor.fetchone()

            if not result or result[0] != current_hash:
                # File is new or has changed
                new_version = (result[1] + 1) if result else 1

                # Deactivate previous versions
                cursor.execute(
                    "UPDATE document_audit SET is_active = 0 WHERE file_path = ?",
                    (file_path,),
                )

                # Insert new version
                cursor.execute(
                    "INSERT INTO document_audit (file_path, file_hash, author, version_number, is_active) VALUES (?, ?, ?, ?, 1)",
                    (file_path, current_hash, author, new_version),
                )
                conn.commit()

                return {
                    "file_path": file_path,
                    "hash": current_hash,
                    "version": new_version,
                    "author": author,
                    "status": "updated" if result else "created",
                }

            return None

    def get_audit_log(self, limit: int = 100) -> list:
        """Retrieve audit log entries"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT file_path, file_hash, author, timestamp, version_number, is_active 
                   FROM document_audit 
                   ORDER BY timestamp DESC 
                   LIMIT ?""",
                (limit,),
            )
            results = cursor.fetchall()

            return [
                {
                    "file_path": row[0],
                    "hash": row[1],
                    "author": row[2],
                    "timestamp": row[3],
                    "version": row[4],
                    "is_active": bool(row[5]),
                }
                for row in results
            ]


if __name__ == "__main__":
    # Test audit manager
    manager = AuditManager()
    print("Database initialized.")
