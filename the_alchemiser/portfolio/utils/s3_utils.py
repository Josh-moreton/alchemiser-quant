#!/usr/bin/env python3
"""Business Unit: portfolio | Status: current.

S3 Utilities for Quantitative Trading System
Handles reading and writing files to S3 storage.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class S3Handler:
    """Handles S3 operations for the quantitative trading system."""

    def __init__(self) -> None:
        """Initialize S3 client."""
        try:
            self.s3_client = boto3.client("s3")
            logging.debug("S3 client initialized successfully")
        except NoCredentialsError:
            logging.error("AWS credentials not found. Please configure AWS credentials.")
            raise
        except Exception as e:
            logging.error(f"Error initializing S3 client: {e}")
            raise

    def parse_s3_uri(self, s3_uri: str) -> tuple[str, str]:
        """Parse S3 URI to extract bucket and key."""
        parsed = urlparse(s3_uri)
        if parsed.scheme != "s3":
            raise ValueError(f"Invalid S3 URI: {s3_uri}. Must start with 's3://'")

        bucket = parsed.netloc
        key = parsed.path.lstrip("/")

        return bucket, key

    def write_text(self, s3_uri: str, content: str) -> bool:
        """Write text content to S3."""
        try:
            bucket, key = self.parse_s3_uri(s3_uri)

            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=content.encode("utf-8"),
                ContentType="text/plain",
            )

            logging.debug(f"Successfully wrote to {s3_uri}")
            return True

        except Exception as e:
            logging.error(f"Error writing to {s3_uri}: {e}")
            return False

    def read_text(self, s3_uri: str) -> str | None:
        """Read text content from S3."""
        try:
            bucket, key = self.parse_s3_uri(s3_uri)

            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            content = response["Body"].read().decode("utf-8")

            logging.debug(f"Successfully read from {s3_uri}")
            return str(content)

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logging.debug(f"File not found: {s3_uri}")
                return None
            logging.error(f"Error reading from {s3_uri}: {e}")
            return None
        except Exception as e:
            logging.error(f"Error reading from {s3_uri}: {e}")
            return None

    def write_json(self, s3_uri: str, data: dict[str, Any]) -> bool:
        """Write JSON data to S3."""
        try:
            json_content = json.dumps(data, indent=2, default=str)
            return self.write_text(s3_uri, json_content)
        except Exception as e:
            logging.error(f"Error serializing JSON for {s3_uri}: {e}")
            return False

    def read_json(self, s3_uri: str) -> dict[str, Any] | None:
        """Read JSON data from S3."""
        try:
            content = self.read_text(s3_uri)
            if content is None:
                return None

            return dict(json.loads(content))

        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON from {s3_uri}: {e}")
            return None
        except Exception as e:
            logging.error(f"Error reading JSON from {s3_uri}: {e}")
            return None

    def append_text(self, s3_uri: str, content: str) -> bool:
        """Append text to an S3 file (reads existing, appends, writes back)."""
        try:
            # Read existing content
            existing_content = self.read_text(s3_uri) or ""

            # Append new content
            new_content = existing_content + content

            # Write back
            return self.write_text(s3_uri, new_content)

        except Exception as e:
            logging.error(f"Error appending to {s3_uri}: {e}")
            return False

    def file_exists(self, s3_uri: str) -> bool:
        """Check if file exists in S3."""
        try:
            bucket, key = self.parse_s3_uri(s3_uri)

            self.s3_client.head_object(Bucket=bucket, Key=key)
            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            logging.error(f"Error checking if {s3_uri} exists: {e}")
            return False
        except Exception as e:
            logging.error(f"Error checking if {s3_uri} exists: {e}")
            return False

    def create_bucket_if_not_exists(self, bucket_name: str, region: str = "us-east-1") -> bool:
        """Create S3 bucket if it doesn't exist."""
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=bucket_name)
            logging.debug(f"Bucket {bucket_name} already exists")
            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                # Bucket doesn't exist, create it
                try:
                    if region == "us-east-1":
                        self.s3_client.create_bucket(Bucket=bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=bucket_name,
                            CreateBucketConfiguration={"LocationConstraint": region},
                        )

                    logging.debug(f"Created bucket {bucket_name}")
                    return True

                except Exception as create_error:
                    logging.error(f"Error creating bucket {bucket_name}: {create_error}")
                    return False
            else:
                logging.error(f"Error checking bucket {bucket_name}: {e}")
                return False


# Global S3 handler instance
_s3_handler: S3Handler | None = None


def get_s3_handler() -> S3Handler:
    """Get or create global S3 handler instance."""
    global _s3_handler
    if _s3_handler is None:
        _s3_handler = S3Handler()
    return _s3_handler


class S3FileHandler(logging.Handler):
    """Custom logging handler that writes to S3."""

    def __init__(self, s3_uri: str) -> None:
        """Create the handler and ensure the target bucket exists."""
        super().__init__()
        self.s3_uri = s3_uri
        self.s3_handler = get_s3_handler()

        # Parse bucket from URI to ensure it exists
        bucket, _ = self.s3_handler.parse_s3_uri(s3_uri)
        self.s3_handler.create_bucket_if_not_exists(bucket)

    def emit(self, record: logging.LogRecord) -> None:
        """Write log record to S3."""
        try:
            log_entry = self.format(record) + "\n"
            self.s3_handler.append_text(self.s3_uri, log_entry)
        except Exception as e:
            # Don't let logging errors crash the application
            # Use basic logging as fallback - don't use print for infrastructure errors
            import logging

            fallback_logger = logging.getLogger(__name__)
            fallback_logger.error(f"S3 logging handler failed: {e}", exc_info=True)


def replace_file_handlers_with_s3(logger: logging.Logger, s3_uri_map: dict[str, str]) -> None:
    """Replace file handlers in a logger with S3 handlers."""
    # Remove existing file handlers
    handlers_to_remove = []
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handlers_to_remove.append(handler)

    for handler in handlers_to_remove:
        logger.removeHandler(handler)

    # Add S3 handlers
    for _log_type, s3_uri in s3_uri_map.items():
        s3_handler = S3FileHandler(s3_uri)
        s3_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(s3_handler)
