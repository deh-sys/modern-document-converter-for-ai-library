"""
Registrar Service - Document Processor

SQLite-based registry for tracking documents, codes, metadata, and processing status.

Architecture:
    - Single SQLite database: registry/master.db
    - ACID transactions for data integrity
    - WAL mode for concurrent access
    - Schema: documents, codes, metadata, processing_steps, registry_state

Features:
    - Code allocation and tracking
    - Document registration and lifecycle
    - Metadata storage (flexible key-value)
    - Processing step history
    - Atomic operations with rollback support

Usage:
    from src.services.registrar import Registrar

    registrar = Registrar()
    doc_id = registrar.register_document(Path("file.pdf"))
    code = "ABCDE"
    registrar.allocate_code(code)
    registrar.commit_code_to_document(code, doc_id)
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from src.core.models import (
    Document,
    DocumentType,
    ProcessingStatus,
    MetadataField,
    ExtractionSource,
    ConfidenceLevel,
)


# ============================================================================
# DATABASE SCHEMA
# ============================================================================

SCHEMA_SQL = """
-- System state table (stores next_code_index and other singleton values)
CREATE TABLE IF NOT EXISTS registry_state (
    key TEXT PRIMARY KEY,
    value INTEGER NOT NULL
);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    original_name TEXT NOT NULL,
    current_name TEXT NOT NULL,
    document_type TEXT,
    unique_code TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Metadata table (flexible key-value for extracted fields)
CREATE TABLE IF NOT EXISTS metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    source TEXT,
    confidence TEXT,
    extractor_name TEXT,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Processing steps table (track pipeline execution)
CREATE TABLE IF NOT EXISTS processing_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    step_name TEXT NOT NULL,
    step_order INTEGER NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Codes allocation table (track code usage and availability)
CREATE TABLE IF NOT EXISTS codes (
    code TEXT PRIMARY KEY,
    document_id INTEGER,
    allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'allocated',
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_code ON documents(unique_code);
CREATE INDEX IF NOT EXISTS idx_documents_path ON documents(file_path);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_metadata_document ON metadata(document_id);
CREATE INDEX IF NOT EXISTS idx_metadata_key ON metadata(key);
CREATE INDEX IF NOT EXISTS idx_codes_status ON codes(status);
CREATE INDEX IF NOT EXISTS idx_codes_document ON codes(document_id);
CREATE INDEX IF NOT EXISTS idx_steps_document ON processing_steps(document_id);
"""


# ============================================================================
# REGISTRAR SERVICE
# ============================================================================

class Registrar:
    """
    SQLite-based registry manager for document tracking and code allocation.

    Schema:
        - registry_state: System state (next_code_index, etc.)
        - documents: File paths, names, types, codes
        - metadata: Extracted fields with provenance
        - processing_steps: Pipeline execution history
        - codes: Code allocation and availability tracking

    Features:
        - Atomic code allocation with rollback
        - Document lifecycle tracking
        - Flexible metadata storage
        - Transaction support for batch operations
        - WAL mode for concurrent access

    Example:
        registrar = Registrar()

        # Register document
        doc_id = registrar.register_document(Path("file.pdf"))

        # Allocate code
        code = "ABCDE"
        registrar.allocate_code(code)

        # Link code to document
        registrar.commit_code_to_document(code, doc_id)
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize registrar with SQLite database.

        Args:
            db_path: Path to database file (default: registry/master.db)
        """
        if db_path is None:
            db_path = Path("registry/master.db")

        # Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize database schema and enable WAL mode."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        # Enable WAL mode for concurrent access
        self.conn.execute("PRAGMA journal_mode=WAL")

        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys=ON")

        # Create schema
        self.conn.executescript(SCHEMA_SQL)
        self.conn.commit()

        # Initialize next_code_index if not present
        cursor = self.conn.execute(
            "SELECT value FROM registry_state WHERE key = 'next_code_index'"
        )
        if cursor.fetchone() is None:
            self.conn.execute(
                "INSERT INTO registry_state (key, value) VALUES ('next_code_index', 0)"
            )
            self.conn.commit()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    @contextmanager
    def transaction(self):
        """
        Context manager for atomic transactions.

        Example:
            with registrar.transaction():
                registrar.allocate_code("ABCDE")
                registrar.register_document(Path("file.pdf"))
                # Both operations succeed or both roll back
        """
        try:
            yield
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    # ========================================================================
    # CODE MANAGEMENT METHODS
    # ========================================================================

    def get_next_code_index(self) -> int:
        """
        Get current code index without incrementing.

        Returns:
            Current next_code_index value
        """
        cursor = self.conn.execute(
            "SELECT value FROM registry_state WHERE key = 'next_code_index'"
        )
        row = cursor.fetchone()
        return row["value"] if row else 0

    def increment_code_index(self) -> int:
        """
        Atomically increment and return code index.

        Returns:
            Previous index value (use this for code generation)

        Example:
            index = registrar.increment_code_index()
            # index = 0, next call returns 1, etc.
        """
        with self.transaction():
            # Get current value
            current = self.get_next_code_index()

            # Increment
            self.conn.execute(
                "UPDATE registry_state SET value = value + 1 WHERE key = 'next_code_index'"
            )

            return current

    def allocate_code(self, code: str) -> None:
        """
        Reserve code in codes table.

        Args:
            code: 5-letter code to allocate

        Raises:
            sqlite3.IntegrityError: If code already exists
        """
        self.conn.execute(
            """
            INSERT INTO codes (code, status, allocated_at)
            VALUES (?, 'allocated', ?)
            """,
            (code, datetime.utcnow()),
        )
        self.conn.commit()

    def code_exists(self, code: str) -> bool:
        """
        Check if code is already allocated.

        Args:
            code: Code to check

        Returns:
            True if code exists in codes table
        """
        cursor = self.conn.execute("SELECT code FROM codes WHERE code = ?", (code,))
        return cursor.fetchone() is not None

    def commit_code_to_document(self, code: str, document_id: int) -> None:
        """
        Link code to document and mark as in_use.

        Args:
            code: 5-letter code
            document_id: Document ID to link

        Example:
            code = "ABCDE"
            registrar.allocate_code(code)
            doc_id = registrar.register_document(Path("file.pdf"))
            registrar.commit_code_to_document(code, doc_id)
        """
        with self.transaction():
            # Update code record
            self.conn.execute(
                """
                UPDATE codes
                SET document_id = ?, status = 'in_use'
                WHERE code = ?
                """,
                (document_id, code),
            )

            # Update document record
            self.conn.execute(
                """
                UPDATE documents
                SET unique_code = ?, updated_at = ?
                WHERE id = ?
                """,
                (code, datetime.utcnow(), document_id),
            )

    def rollback_code(self, code: str) -> None:
        """
        Delete uncommitted code allocation.

        Only deletes if code is not linked to a document.

        Args:
            code: Code to rollback
        """
        self.conn.execute(
            """
            DELETE FROM codes
            WHERE code = ? AND document_id IS NULL AND status = 'allocated'
            """,
            (code,),
        )
        self.conn.commit()

    def get_allocated_codes_count(self) -> int:
        """
        Get total number of allocated codes.

        Returns:
            Count of codes in codes table
        """
        cursor = self.conn.execute("SELECT COUNT(*) as count FROM codes")
        row = cursor.fetchone()
        return row["count"] if row else 0

    # ========================================================================
    # DOCUMENT MANAGEMENT METHODS
    # ========================================================================

    def register_document(
        self,
        file_path: Path,
        document_type: Optional[DocumentType] = None,
        code: Optional[str] = None,
    ) -> int:
        """
        Register new document in registry.

        Args:
            file_path: Path to document
            document_type: Type of document (optional)
            code: Pre-existing code (optional)

        Returns:
            Document ID

        Example:
            doc_id = registrar.register_document(
                Path("file.pdf"),
                document_type=DocumentType.CASELAW,
                code="ABCDE"
            )
        """
        original_name = file_path.name
        current_name = file_path.name
        doc_type_str = document_type.value if document_type else None

        cursor = self.conn.execute(
            """
            INSERT INTO documents (file_path, original_name, current_name, document_type, unique_code)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(file_path), original_name, current_name, doc_type_str, code),
        )
        self.conn.commit()

        return cursor.lastrowid

    def get_document_by_path(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Retrieve document by file path.

        Args:
            file_path: Path to document

        Returns:
            Document record as dict, or None if not found
        """
        cursor = self.conn.execute(
            "SELECT * FROM documents WHERE file_path = ?", (str(file_path),)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_document_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve document by unique code.

        Args:
            code: 5-letter unique code

        Returns:
            Document record as dict, or None if not found
        """
        cursor = self.conn.execute(
            "SELECT * FROM documents WHERE unique_code = ?", (code,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_document_by_id(self, document_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve document by ID.

        Args:
            document_id: Document ID

        Returns:
            Document record as dict, or None if not found
        """
        cursor = self.conn.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_document_name(self, document_id: int, new_name: str) -> None:
        """
        Update document's current_name field.

        Args:
            document_id: Document ID
            new_name: New filename
        """
        self.conn.execute(
            """
            UPDATE documents
            SET current_name = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_name, datetime.utcnow(), document_id),
        )
        self.conn.commit()

    def update_document_type(self, document_id: int, document_type: DocumentType) -> None:
        """
        Update document's type.

        Args:
            document_id: Document ID
            document_type: New document type
        """
        self.conn.execute(
            """
            UPDATE documents
            SET document_type = ?, updated_at = ?
            WHERE id = ?
            """,
            (document_type.value, datetime.utcnow(), document_id),
        )
        self.conn.commit()

    def list_documents(
        self,
        document_type: Optional[DocumentType] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        List documents with optional filtering.

        Args:
            document_type: Filter by type (optional)
            limit: Maximum number of results (optional)

        Returns:
            List of document records
        """
        query = "SELECT * FROM documents"
        params = []

        if document_type:
            query += " WHERE document_type = ?"
            params.append(document_type.value)

        query += " ORDER BY created_at DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    # ========================================================================
    # METADATA METHODS
    # ========================================================================

    def add_metadata(
        self,
        document_id: int,
        key: str,
        value: str,
        source: ExtractionSource,
        confidence: ConfidenceLevel,
        extractor_name: Optional[str] = None,
    ) -> None:
        """
        Add metadata field for document.

        Args:
            document_id: Document ID
            key: Metadata key (e.g., "court", "year", "author")
            value: Metadata value
            source: Where metadata came from
            confidence: Confidence level
            extractor_name: Name of extractor that found this field
        """
        self.conn.execute(
            """
            INSERT INTO metadata (document_id, key, value, source, confidence, extractor_name, extracted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                key,
                value,
                source.value,
                confidence.value,
                extractor_name,
                datetime.utcnow(),
            ),
        )
        self.conn.commit()

    def get_metadata(self, document_id: int) -> List[Dict[str, Any]]:
        """
        Get all metadata for document.

        Args:
            document_id: Document ID

        Returns:
            List of metadata records
        """
        cursor = self.conn.execute(
            "SELECT * FROM metadata WHERE document_id = ? ORDER BY extracted_at",
            (document_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    # ========================================================================
    # PROCESSING STEPS METHODS
    # ========================================================================

    def record_processing_step(
        self,
        document_id: int,
        step_name: str,
        step_order: int,
        status: ProcessingStatus,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Record processing step execution.

        Args:
            document_id: Document ID
            step_name: Step name (rename, code, convert, clean)
            step_order: Step order (1-4)
            status: Processing status
            error_message: Error message if failed
        """
        now = datetime.utcnow()

        self.conn.execute(
            """
            INSERT INTO processing_steps (
                document_id, step_name, step_order, status,
                started_at, completed_at, error_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                step_name,
                step_order,
                status.value,
                now,
                now if status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED] else None,
                error_message,
            ),
        )
        self.conn.commit()

    def get_processing_steps(self, document_id: int) -> List[Dict[str, Any]]:
        """
        Get all processing steps for document.

        Args:
            document_id: Document ID

        Returns:
            List of processing step records
        """
        cursor = self.conn.execute(
            "SELECT * FROM processing_steps WHERE document_id = ? ORDER BY step_order",
            (document_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dict with counts and statistics

        Example:
            stats = registrar.get_statistics()
            print(f"Total documents: {stats['total_documents']}")
            print(f"Allocated codes: {stats['allocated_codes']}")
        """
        stats = {}

        # Total documents
        cursor = self.conn.execute("SELECT COUNT(*) as count FROM documents")
        stats["total_documents"] = cursor.fetchone()["count"]

        # Documents by type
        cursor = self.conn.execute(
            "SELECT document_type, COUNT(*) as count FROM documents GROUP BY document_type"
        )
        stats["by_type"] = {row["document_type"]: row["count"] for row in cursor.fetchall()}

        # Total codes
        cursor = self.conn.execute("SELECT COUNT(*) as count FROM codes")
        stats["allocated_codes"] = cursor.fetchone()["count"]

        # Code status
        cursor = self.conn.execute(
            "SELECT status, COUNT(*) as count FROM codes GROUP BY status"
        )
        stats["code_status"] = {row["status"]: row["count"] for row in cursor.fetchall()}

        # Next code index
        stats["next_code_index"] = self.get_next_code_index()

        return stats

    def export_to_json(self, output_path: Path) -> None:
        """
        Export registry to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        import json

        data = {
            "documents": self.list_documents(),
            "statistics": self.get_statistics(),
        }

        with output_path.open("w") as f:
            json.dump(data, f, indent=2, default=str)
