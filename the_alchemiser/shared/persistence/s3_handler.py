#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Amazon S3 Handler for Live Trading Persistence.

Typed implementation of the `PersistenceHandler` protocol using boto3. URIs must be
in the form `s3://bucket/key/path.ext`. Credentials and region are sourced from the
standard AWS environment configuration.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib.parse import urlparse


class S3Handler:
    """S3-backed persistence handler for live trading mode."""

    def __init__(self) -> None:
        """Initialize an S3 client using environment configuration."""
        import boto3  # type: ignore[import-not-found]

        self._s3 = boto3.client("s3")

    def _parse_s3_uri(self, uri: str) -> tuple[str, str]:
        """Parse an S3 URI into bucket and key.

        Args:
            uri: S3 URI in the form `s3://bucket/key`

        Returns:
            Tuple of (bucket, key)

        Raises:
            ValueError: If the URI is not a valid s3:// URI

        """
        if not uri.startswith("s3://"):
            raise ValueError(f"Invalid S3 URI: {uri}")
        parsed = urlparse(uri)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        if not bucket or not key:
            raise ValueError(f"Invalid S3 URI: {uri}")
        return bucket, key

    def write_text(self, uri: str, content: str) -> bool:
        """Write text content to S3.

        Returns True on success, False on failure.
        """
        try:
            bucket, key = self._parse_s3_uri(uri)
            self._s3.put_object(Bucket=bucket, Key=key, Body=content.encode("utf-8"))
            logging.debug(f"Successfully wrote text to s3://{bucket}/{key}")
            return True
        except Exception as e:
            logging.error(f"Error writing text to {uri}: {e}")
            return False

    def read_text(self, uri: str) -> str | None:
        """Read text content from S3. Returns None if missing or on error."""
        try:
            bucket, key = self._parse_s3_uri(uri)
            obj = self._s3.get_object(Bucket=bucket, Key=key)
            body = obj["Body"].read()
            return body.decode("utf-8")
        except self._s3.exceptions.NoSuchKey:  # type: ignore[attr-defined]
            logging.debug(f"S3 object not found: {uri}")
            return None
        except Exception as e:
            logging.error(f"Error reading text from {uri}: {e}")
            return None

    def write_json(self, uri: str, data: dict[str, Any]) -> bool:
        """Serialize dict to JSON and write to S3."""
        try:
            json_content = json.dumps(data, indent=2, default=str)
            return self.write_text(uri, json_content)
        except Exception as e:
            logging.error(f"Error serializing JSON for {uri}: {e}")
            return False

    def read_json(self, uri: str) -> dict[str, Any] | None:
        """Read and parse JSON content from S3."""
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
        """Append text to an S3 object by read-modify-write."""
        try:
            existing = self.read_text(uri) or ""
            new_content = existing + content
            return self.write_text(uri, new_content)
        except Exception as e:
            logging.error(f"Error appending to {uri}: {e}")
            return False

    def file_exists(self, uri: str) -> bool:
        """Check if S3 object exists."""
        try:
            bucket, key = self._parse_s3_uri(uri)
            self._s3.head_object(Bucket=bucket, Key=key)
            return True
        except self._s3.exceptions.NoSuchKey:  # type: ignore[attr-defined]
            return False
        except Exception:
            # HeadObject can raise 404 via ClientError; treat any error as non-existence
            return False
