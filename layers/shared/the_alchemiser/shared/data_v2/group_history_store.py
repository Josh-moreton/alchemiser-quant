"""Business Unit: data | Status: current.

Group history store for S3 Parquet files.

Handles reading, writing, and incremental updates of historical group data
stored as Parquet files in S3. Each group has its own Parquet file containing
all available daily portfolio selections and returns.

This mirrors the MarketDataStore pattern but for group/portfolio history data.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any

import boto3
import pandas as pd
import pyarrow.parquet as pq

from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

logger = get_logger(__name__)

# Module constant for cache directory
CACHE_DIR = Path(tempfile.gettempdir()) / "alchemiser_group_history"


@dataclass(frozen=True)
class GroupMetadata:
    """Metadata for a group's history file in S3.

    Attributes:
        group_id: Group identifier
        last_date: Date of the most recent data in the file
        row_count: Total number of rows in the file
        updated_at: When the metadata was last updated

    """

    group_id: str
    last_date: str  # YYYY-MM-DD format
    row_count: int
    updated_at: str  # ISO format timestamp

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "group_id": self.group_id,
            "last_date": self.last_date,
            "row_count": self.row_count,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GroupMetadata:
        """Create from dictionary."""
        return cls(
            group_id=data["group_id"],
            last_date=data["last_date"],
            row_count=data["row_count"],
            updated_at=data["updated_at"],
        )


class GroupHistoryStore:
    """S3-backed store for historical group data in Parquet format.

    Provides read/write access to group history with incremental update support.
    Data is organized as: s3://{bucket}/group-history/{group_id}/daily.parquet

    Attributes:
        bucket_name: S3 bucket name for market data storage (same as MarketDataBucket)
        region: AWS region for S3 client

    """

    def __init__(
        self,
        bucket_name: str | None = None,
        region: str = "us-east-1",
        s3_client: S3Client | None = None,
    ) -> None:
        """Initialize group history store.

        Args:
            bucket_name: S3 bucket name. If None, reads from MARKET_DATA_BUCKET env var.
            region: AWS region for S3 operations
            s3_client: Optional S3 client for dependency injection (testing)

        Raises:
            ValueError: If bucket_name is not provided and env var is not set

        """
        resolved_bucket = bucket_name or os.environ.get("MARKET_DATA_BUCKET")
        if not resolved_bucket:
            raise ValueError(
                "bucket_name required: provide via parameter or MARKET_DATA_BUCKET env var"
            )

        self.bucket_name: str = resolved_bucket
        self.region = region
        self._s3_client = s3_client

        # Ensure cache directory exists
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        logger.info(
            "GroupHistoryStore initialized",
            bucket=self.bucket_name,
            region=self.region,
        )

    @property
    def s3_client(self) -> S3Client:
        """Lazy-initialized S3 client."""
        if self._s3_client is None:
            self._s3_client = boto3.client("s3", region_name=self.region)
        return self._s3_client

    def _sanitize_group_id_for_path(self, group_id: str) -> str:
        """Sanitize group_id for use in S3 keys and file paths.

        Replaces problematic characters to prevent nested directory issues.

        Args:
            group_id: Raw group identifier

        Returns:
            Sanitized group_id safe for paths

        """
        return group_id.replace("/", "_").replace("\\", "_")

    def _group_data_key(self, group_id: str) -> str:
        """Get S3 key for group's data file."""
        sanitized = self._sanitize_group_id_for_path(group_id)
        return f"group-history/{sanitized}/daily.parquet"

    def _group_metadata_key(self, group_id: str) -> str:
        """Get S3 key for group's metadata file."""
        sanitized = self._sanitize_group_id_for_path(group_id)
        return f"group-history/{sanitized}/metadata.json"

    def _local_cache_path(self, group_id: str) -> Path:
        """Get local cache path for group's data."""
        sanitized = self._sanitize_group_id_for_path(group_id)
        return CACHE_DIR / f"{sanitized}_daily.parquet"

    def _is_cache_valid(self, group_id: str, cache_path: Path) -> bool:
        """Check if local cache is valid against S3 metadata.

        Validates cache by comparing row count in cached file against
        S3 metadata. This prevents warm Lambda invocations from using
        stale data after S3 has been updated.

        Args:
            group_id: Group identifier
            cache_path: Path to local cached parquet file

        Returns:
            True if cache is valid and can be used, False if stale

        """
        if not cache_path.exists():
            return False

        try:
            # Get S3 metadata for comparison
            s3_metadata = self.get_metadata(group_id)
            if s3_metadata is None:
                # No metadata in S3, cache is potentially stale
                logger.warning(
                    "No S3 metadata found, invalidating cache",
                    group_id=group_id,
                )
                return False

            # Read cached file row count (metadata only, not full file)
            cached_metadata = pq.read_metadata(cache_path)
            cached_row_count = cached_metadata.num_rows

            # Compare row counts - invalidate if different (handles both stale and corrupted cache)
            if cached_row_count != s3_metadata.row_count:
                logger.info(
                    "Cache row count mismatch, invalidating cache",
                    group_id=group_id,
                    cached_rows=cached_row_count,
                    s3_rows=s3_metadata.row_count,
                )
                return False

            logger.debug(
                "Cache valid",
                group_id=group_id,
                cached_rows=cached_row_count,
                s3_rows=s3_metadata.row_count,
            )
            return True

        except Exception as e:
            logger.warning(
                "Cache validation failed, will fetch from S3",
                group_id=group_id,
                error=str(e),
            )
            return False

    def get_metadata(self, group_id: str) -> GroupMetadata | None:
        """Get metadata for a group's data file.

        Args:
            group_id: Group identifier

        Returns:
            GroupMetadata if file exists, None otherwise

        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=self._group_metadata_key(group_id),
            )
            data = json.loads(response["Body"].read().decode("utf-8"))
            return GroupMetadata.from_dict(data)
        except self.s3_client.exceptions.NoSuchKey:
            return None
        except Exception as e:
            logger.warning(
                "Failed to get metadata",
                group_id=group_id,
                error=str(e),
            )
            return None

    def _update_metadata(self, group_id: str, df: pd.DataFrame) -> None:
        """Update metadata file for group after data update.

        Args:
            group_id: Group identifier
            df: DataFrame with the group's data

        """
        if df.empty:
            return

        # Get the last date from the DataFrame
        if "record_date" in df.columns:
            last_date = pd.to_datetime(df["record_date"]).max()
        else:
            logger.error(
                "DataFrame missing record_date column",
                group_id=group_id,
            )
            return

        metadata = GroupMetadata(
            group_id=group_id,
            last_date=last_date.strftime("%Y-%m-%d"),
            row_count=len(df),
            updated_at=datetime.now(UTC).isoformat(),
        )

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=self._group_metadata_key(group_id),
            Body=json.dumps(metadata.to_dict()).encode("utf-8"),
            ContentType="application/json",
        )

        logger.debug(
            "Updated metadata",
            group_id=group_id,
            last_date=metadata.last_date,
            row_count=metadata.row_count,
        )

    def read_group_data(self, group_id: str, *, use_cache: bool = True) -> pd.DataFrame | None:
        """Read historical data for a group.

        Args:
            group_id: Group identifier
            use_cache: If True, use local cache when available (validates against S3 metadata)

        Returns:
            DataFrame with group history data, or None if not found

        """
        cache_path = self._local_cache_path(group_id)

        # Check local cache first (with validation against S3 metadata)
        if use_cache and self._is_cache_valid(group_id, cache_path):
            try:
                df = pd.read_parquet(cache_path, engine="pyarrow")
                logger.debug(
                    "Read from validated cache",
                    group_id=group_id,
                    rows=len(df),
                )
                return df
            except Exception as e:
                logger.warning(
                    "Cache read failed, fetching from S3",
                    group_id=group_id,
                    error=str(e),
                )

        # Fetch from S3
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=self._group_data_key(group_id),
            )

            # Write to temp file for pandas to read
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
                    tmp.write(response["Body"].read())
                    tmp_path = tmp.name

                df = pd.read_parquet(tmp_path, engine="pyarrow")

                # Update local cache
                if use_cache:
                    df.to_parquet(cache_path, index=False, engine="pyarrow")

                logger.info(
                    "Read from S3",
                    group_id=group_id,
                    rows=len(df),
                )
                return df

            finally:
                # Clean up temp file
                if tmp_path is not None:
                    Path(tmp_path).unlink(missing_ok=True)

        except self.s3_client.exceptions.NoSuchKey:
            logger.debug("No data found for group", group_id=group_id)
            return None
        except Exception as e:
            logger.error(
                "Failed to read group data",
                group_id=group_id,
                error=str(e),
            )
            return None

    def write_group_data(self, group_id: str, df: pd.DataFrame) -> bool:
        """Write historical data for a group.

        Args:
            group_id: Group identifier
            df: DataFrame with group history data

        Returns:
            True if successful, False otherwise

        """
        if df.empty:
            logger.warning("Attempted to write empty DataFrame", group_id=group_id)
            return False

        tmp_path = None
        try:
            # Write to temp file first
            with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
                df.to_parquet(tmp.name, index=False, compression="snappy", engine="pyarrow")
                tmp_path = Path(tmp.name)

            # Upload to S3
            with tmp_path.open("rb") as f:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=self._group_data_key(group_id),
                    Body=f.read(),
                    ContentType="application/octet-stream",
                )

            # Update metadata
            self._update_metadata(group_id, df)

            # Update local cache
            cache_path = self._local_cache_path(group_id)
            df.to_parquet(cache_path, index=False, engine="pyarrow")

            logger.info(
                "Wrote group data to S3",
                group_id=group_id,
                rows=len(df),
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to write group data",
                group_id=group_id,
                error=str(e),
            )
            return False

        finally:
            # Clean up temp file
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)

    def append_records(
        self,
        group_id: str,
        new_records: pd.DataFrame,
    ) -> bool:
        """Append new records to existing group history.

        Args:
            group_id: Group identifier
            new_records: DataFrame with new records to append

        Returns:
            True if successful, False otherwise

        """
        if new_records.empty:
            logger.debug("No new records to append", group_id=group_id)
            return True

        # Read existing data
        existing_df = self.read_group_data(group_id, use_cache=False)

        if existing_df is None:
            # No existing data, write new records
            return self.write_group_data(group_id, new_records)

        # Ensure record_date column exists in both
        if "record_date" not in existing_df.columns or "record_date" not in new_records.columns:
            logger.error(
                "Missing record_date column for deduplication",
                group_id=group_id,
            )
            return False

        # Convert dates for comparison
        existing_df["record_date"] = pd.to_datetime(existing_df["record_date"])
        new_records["record_date"] = pd.to_datetime(new_records["record_date"])

        # Get existing dates
        existing_dates = set(existing_df["record_date"].dt.date)
        new_dates = set(new_records["record_date"].dt.date)

        # Filter to truly new dates only
        truly_new_dates = new_dates - existing_dates

        if not truly_new_dates:
            logger.debug("All records already up to date", group_id=group_id)
            return True

        # Filter new records to include only truly new dates
        new_records_to_add = new_records[
            new_records["record_date"].dt.date.isin(truly_new_dates)
        ]

        # Combine and sort by date
        combined_df = pd.concat([existing_df, new_records_to_add], ignore_index=True)
        combined_df = combined_df.sort_values("record_date").reset_index(drop=True)

        logger.info(
            "Appending records",
            group_id=group_id,
            existing_rows=len(existing_df),
            new_dates=len(truly_new_dates),
            final_rows=len(combined_df),
        )

        return self.write_group_data(group_id, combined_df)

    def list_groups(self) -> list[str]:
        """List all groups that have data in S3.

        Returns:
            List of group identifiers with data files

        """
        groups: list[str] = []
        paginator = self.s3_client.get_paginator("list_objects_v2")

        for page in paginator.paginate(
            Bucket=self.bucket_name, Prefix="group-history/", Delimiter="/"
        ):
            for prefix in page.get("CommonPrefixes", []):
                # Extract group_id from prefix like "group-history/GROUP_ID/"
                group_path = prefix["Prefix"].rstrip("/")
                group_id = group_path.split("/")[-1]
                groups.append(group_id)

        logger.debug("Listed groups", count=len(groups))
        return sorted(groups)
