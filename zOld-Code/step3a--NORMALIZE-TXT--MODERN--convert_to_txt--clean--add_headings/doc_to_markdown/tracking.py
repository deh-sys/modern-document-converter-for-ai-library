"""
Persistent tracking system for document conversions.

This module provides a SQLite-based tracking database to record conversion history,
detect file modifications, and prevent duplicate processing.
"""

import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)


class ConversionTracker:
    """Manages persistent tracking of file conversions using SQLite."""

    DB_NAME = "doc_to_markdown_history.db"
    REGISTRY_DIR = Path("/Users/dan/LIBRARY_SYSTEM_REGISTRIES")

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the conversion tracker.

        Args:
            db_path: Path to the SQLite database file. If None, uses centralized registry directory.
        """
        if db_path is None:
            # Ensure registry directory exists
            self.REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
            db_path = self.REGISTRY_DIR / self.DB_NAME
        else:
            db_path = Path(db_path)

        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Initialize the database schema if it doesn't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_path TEXT NOT NULL,
                        source_mtime REAL NOT NULL,
                        source_size INTEGER NOT NULL,
                        output_path TEXT NOT NULL,
                        conversion_date TEXT NOT NULL,
                        status TEXT NOT NULL,
                        file_hash TEXT,
                        UNIQUE(source_path)
                    )
                """)

                # Create index for faster lookups
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_source_path
                    ON conversions(source_path)
                """)

                conn.commit()
                logger.debug(f"Database initialized at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def add_conversion_record(
        self,
        source_path: Path,
        output_path: Path,
        status: str = "success"
    ) -> None:
        """
        Add or update a conversion record in the database.

        Args:
            source_path: Path to the source document
            output_path: Path to the generated markdown file
            status: Conversion status ("success" or "failed")
        """
        try:
            source_path = Path(source_path).resolve()
            output_path = Path(output_path).resolve()

            if not source_path.exists():
                logger.warning(f"Source file does not exist: {source_path}")
                return

            stat = source_path.stat()
            source_mtime = stat.st_mtime
            source_size = stat.st_size
            file_hash = self._compute_file_hash(source_path)
            conversion_date = datetime.now().isoformat()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO conversions
                    (source_path, source_mtime, source_size, output_path,
                     conversion_date, status, file_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(source_path),
                    source_mtime,
                    source_size,
                    str(output_path),
                    conversion_date,
                    status,
                    file_hash
                ))
                conn.commit()
                logger.debug(f"Recorded conversion: {source_path} -> {output_path}")
        except sqlite3.Error as e:
            logger.error(f"Failed to add conversion record: {e}")
        except Exception as e:
            logger.error(f"Unexpected error adding conversion record: {e}")

    def get_conversion_record(self, source_path: Path) -> Optional[Dict[str, Any]]:
        """
        Retrieve the conversion record for a source file.

        Args:
            source_path: Path to the source document

        Returns:
            Dictionary with conversion record or None if not found
        """
        try:
            source_path = Path(source_path).resolve()

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM conversions WHERE source_path = ?
                """, (str(source_path),))

                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve conversion record: {e}")
            return None

    def is_file_modified(self, source_path: Path) -> bool:
        """
        Check if a source file has been modified since last conversion.

        Args:
            source_path: Path to the source document

        Returns:
            True if file is modified or no record exists, False if unchanged
        """
        try:
            source_path = Path(source_path).resolve()

            if not source_path.exists():
                return False

            record = self.get_conversion_record(source_path)
            if not record:
                # No record means it's a new file
                return True

            # Compare modification time
            current_mtime = source_path.stat().st_mtime
            recorded_mtime = record['source_mtime']

            # File is considered modified if mtime is newer
            # Use a small epsilon to account for filesystem timestamp precision
            return current_mtime > recorded_mtime + 0.01

        except Exception as e:
            logger.error(f"Error checking file modification: {e}")
            return True  # Assume modified on error (safer)

    def was_conversion_successful(self, source_path: Path) -> bool:
        """
        Check if the last conversion of a file was successful.

        Args:
            source_path: Path to the source document

        Returns:
            True if last conversion was successful, False otherwise
        """
        record = self.get_conversion_record(source_path)
        return record is not None and record['status'] == 'success'

    def cleanup_stale_records(self) -> int:
        """
        Remove records for source files that no longer exist.

        Returns:
            Number of records removed
        """
        try:
            removed_count = 0

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, source_path FROM conversions")
                records = cursor.fetchall()

                for record_id, source_path in records:
                    if not Path(source_path).exists():
                        cursor.execute("DELETE FROM conversions WHERE id = ?", (record_id,))
                        removed_count += 1

                conn.commit()

            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} stale record(s)")

            return removed_count
        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup stale records: {e}")
            return 0

    def get_all_records(self) -> list[Dict[str, Any]]:
        """
        Retrieve all conversion records.

        Returns:
            List of all conversion records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM conversions ORDER BY conversion_date DESC")
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve all records: {e}")
            return []

    def clear_all_records(self) -> None:
        """Clear all conversion records from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM conversions")
                conn.commit()
                logger.info("Cleared all conversion records")
        except sqlite3.Error as e:
            logger.error(f"Failed to clear records: {e}")

    def _compute_file_hash(self, file_path: Path, chunk_size: int = 8192) -> str:
        """
        Compute SHA256 hash of a file.

        Args:
            file_path: Path to the file
            chunk_size: Size of chunks to read

        Returns:
            Hexadecimal hash string
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Failed to compute file hash: {e}")
            return ""

    def get_statistics(self) -> Dict[str, int]:
        """
        Get conversion statistics.

        Returns:
            Dictionary with statistics (total, successful, failed)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM conversions")
                total = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM conversions WHERE status = 'success'")
                successful = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM conversions WHERE status = 'failed'")
                failed = cursor.fetchone()[0]

                return {
                    'total': total,
                    'successful': successful,
                    'failed': failed
                }
        except sqlite3.Error as e:
            logger.error(f"Failed to get statistics: {e}")
            return {'total': 0, 'successful': 0, 'failed': 0}
