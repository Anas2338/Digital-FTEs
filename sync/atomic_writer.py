"""
Atomic Write Pattern for Platinum Tier

Ensures no partial file writes during vault synchronization.
Implements write-to-temp-then-rename pattern for data integrity.

Based on research.md and spec.md FR-019a: Prevents partial file writes
that could corrupt vault state during sync operations.
"""

import os
import tempfile
from pathlib import Path
from typing import Union


class AtomicWriter:
    """
    Provides atomic file write operations using temp-file-then-rename pattern.

    Guarantees:
    - Either complete write succeeds or no changes are made
    - No partial file contents visible to other processes
    - Safe for concurrent reads during write
    """

    @staticmethod
    def write(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> None:
        """
        Atomically write content to file.

        Process:
        1. Write to temporary file in same directory
        2. Flush and sync to disk
        3. Atomically rename temp file to target (replaces existing)

        Args:
            file_path: Target file path
            content: Content to write
            encoding: Text encoding (default utf-8)

        Raises:
            OSError: If write or rename fails
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create temp file in same directory (ensures same filesystem for atomic rename)
        fd, temp_path = tempfile.mkstemp(
            dir=file_path.parent,
            prefix=f".{file_path.name}.",
            suffix=".tmp"
        )

        try:
            # Write content to temp file
            with os.fdopen(fd, 'w', encoding=encoding) as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())  # Ensure written to disk

            # Atomic rename (replaces existing file if present)
            os.replace(temp_path, file_path)

        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

    @staticmethod
    def write_bytes(file_path: Union[str, Path], content: bytes) -> None:
        """
        Atomically write binary content to file.

        Args:
            file_path: Target file path
            content: Binary content to write

        Raises:
            OSError: If write or rename fails
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        fd, temp_path = tempfile.mkstemp(
            dir=file_path.parent,
            prefix=f".{file_path.name}.",
            suffix=".tmp"
        )

        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())

            os.replace(temp_path, file_path)

        except Exception:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

    @staticmethod
    def append(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> None:
        """
        Atomically append content to file.

        Note: Reads entire file into memory. Not suitable for very large files.

        Args:
            file_path: Target file path
            content: Content to append
            encoding: Text encoding (default utf-8)

        Raises:
            OSError: If read, write, or rename fails
        """
        file_path = Path(file_path)

        # Read existing content if file exists
        existing_content = ""
        if file_path.exists():
            existing_content = file_path.read_text(encoding=encoding)

        # Write combined content atomically
        AtomicWriter.write(file_path, existing_content + content, encoding=encoding)
