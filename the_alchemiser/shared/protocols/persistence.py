#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Storage Protocol Interface for Trading System Persistence.

This module defines the protocol for storage operations, allowing
different implementations (S3, local files, no-op) based on trading mode.
"""

from __future__ import annotations

from typing import Any, Protocol


class PersistenceHandler(Protocol):
    """Protocol for persistence operations in the trading system."""

    def write_text(self, uri: str, content: str) -> bool:
        """Write text content to storage.

        Args:
            uri: Storage location URI
            content: Text content to write

        Returns:
            True if successful, False otherwise

        """
        ...

    def read_text(self, uri: str) -> str | None:
        """Read text content from storage.

        Args:
            uri: Storage location URI

        Returns:
            Content string if found, None otherwise

        """
        ...

    def write_json(self, uri: str, data: dict[str, str | int | bool | None]) -> bool:
        """Write JSON data to storage.

        Args:
            uri: Storage location URI
            data: Dictionary to serialize as JSON

        Returns:
            True if successful, False otherwise

        """
        ...

    def read_json(self, uri: str) -> dict[str, Any] | None:
        """Read JSON data from storage.

        Args:
            uri: Storage location URI

        Returns:
            Deserialized dictionary if found, None otherwise

        """
        ...

    def append_text(self, uri: str, content: str) -> bool:
        """Append text to storage location.

        Args:
            uri: Storage location URI
            content: Text content to append

        Returns:
            True if successful, False otherwise

        """
        ...

    def file_exists(self, uri: str) -> bool:
        """Check if file exists in storage.

        Args:
            uri: Storage location URI

        Returns:
            True if file exists, False otherwise

        """
        ...
