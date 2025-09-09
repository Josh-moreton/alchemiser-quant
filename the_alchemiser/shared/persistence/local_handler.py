#!/usr/bin/env python3
"""Business Unit: shared | Status: current

Local File Handler for Paper Trading Persistence.

This module provides local file-based storage for paper trading mode,
avoiding S3 dependencies while maintaining the same interface.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class LocalFileHandler:
    """Local file-based storage handler for paper trading mode."""

    def __init__(self, base_path: str | None = None) -> None:
        """Initialize local file handler.

        Args:
            base_path: Base directory for storing files. If None, uses a secure temp directory.

        """
        if base_path is None:
            import tempfile

            # Create a secure temporary directory
            temp_dir = tempfile.mkdtemp(prefix="alchemiser_paper_")
            self.base_path = Path(temp_dir)
        else:
            self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logging.debug(f"LocalFileHandler initialized with base path: {self.base_path}")

    def _uri_to_path(self, uri: str) -> Path:
        """Convert storage URI to local file path.

        Args:
            uri: Storage URI (s3://bucket/path or file:///path format)

        Returns:
            Local Path object

        """
        if uri.startswith("s3://"):
            # Convert S3 URI to local path
            parsed = urlparse(uri)
            bucket = parsed.netloc
            key = parsed.path.lstrip("/")
            return self.base_path / bucket / key
        if uri.startswith("file://"):
            # Handle file URI
            return Path(uri[7:])  # Remove file:// prefix
        # Treat as relative path
        return self.base_path / uri.lstrip("/")

    def write_text(self, uri: str, content: str) -> bool:
        """Write text content to local file."""
        try:
            file_path = self._uri_to_path(uri)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            file_path.write_text(content, encoding="utf-8")
            logging.debug(f"Successfully wrote text to {file_path}")
            return True

        except Exception as e:
            logging.error(f"Error writing text to {uri}: {e}")
            return False

    def read_text(self, uri: str) -> str | None:
        """Read text content from local file."""
        try:
            file_path = self._uri_to_path(uri)

            if not file_path.exists():
                logging.debug(f"File not found: {file_path}")
                return None

            content = file_path.read_text(encoding="utf-8")
            logging.debug(f"Successfully read text from {file_path}")
            return content

        except Exception as e:
            logging.error(f"Error reading text from {uri}: {e}")
            return None

    def write_json(self, uri: str, data: dict[str, Any]) -> bool:
        """Write JSON data to local file."""
        try:
            json_content = json.dumps(data, indent=2, default=str)
            return self.write_text(uri, json_content)
        except Exception as e:
            logging.error(f"Error serializing JSON for {uri}: {e}")
            return False

    def read_json(self, uri: str) -> dict[str, Any] | None:
        """Read JSON data from local file."""
        try:
            content = self.read_text(uri)
            if content is None:
                return None

            return dict(json.loads(content))

        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON from {uri}: {e}")
            return None
        except Exception as e:
            logging.error(f"Error reading JSON from {uri}: {e}")
            return None

    def append_text(self, uri: str, content: str) -> bool:
        """Append text to local file."""
        try:
            # Read existing content
            existing_content = self.read_text(uri) or ""

            # Append new content
            new_content = existing_content + content

            # Write back
            return self.write_text(uri, new_content)

        except Exception as e:
            logging.error(f"Error appending to {uri}: {e}")
            return False

    def file_exists(self, uri: str) -> bool:
        """Check if local file exists."""
        try:
            file_path = self._uri_to_path(uri)
            return file_path.exists()
        except Exception as e:
            logging.error(f"Error checking if {uri} exists: {e}")
            return False

    def create_bucket_if_not_exists(self, bucket_name: str, region: str = "us-east-1") -> bool:
        """Create bucket directory if it doesn't exist (local equivalent)."""
        try:
            bucket_path = self.base_path / bucket_name
            bucket_path.mkdir(parents=True, exist_ok=True)
            logging.debug(f"Created/verified bucket directory: {bucket_path}")
            return True
        except Exception as e:
            logging.error(f"Error creating bucket directory {bucket_name}: {e}")
            return False
