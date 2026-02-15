"""Business Unit: data | Status: current.

Group history store for S3 Parquet files.

Handles reading, writing, and incremental updates of historical group performance
data stored as Parquet files in S3. Each group has its own Parquet file containing
all available daily returns and selections, similar to how individual ticker data
is stored in MarketDataStore.

Data Format:
    - Each row represents one trading day
    - Columns: record_date, portfolio_daily_return, selections (JSON), group_id
    - Parquet file per group: s3://{bucket}/groups/{group_id}/history.parquet
    - Metadata file per group: s3://{bucket}/groups/{group_id}/metadata.json
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
        last_record_date: Date of the most recent record in the file (YYYY-MM-DD)
        row_count: Total number of records in the file
        updated_at: When the metadata was last updated (ISO format timestamp)

    """

    group_id: str
    last_record_date: str  # YYYY-MM-DD format
    row_count: int
    updated_at: str  # ISO format timestamp

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "group_id": self.group_id,
            "last_record_date": self.last_record_date,
            "row_count": self.row_count,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GroupMetadata:
        """Create from dictionary."""
        return cls(
            group_id=data["group_id"],
            last_record_date=data["last_record_date"],
            row_count=data["row_count"],
            updated_at=data["updated_at"],
        )


class GroupHistoryStore:
    """S3-backed store for historical group performance data in Parquet format.

    Provides read/write access to group history with incremental update support.
    Data is organized as: s3://{bucket}/groups/{group_id}/history.parquet

    Attributes:
        bucket_name: S3 bucket name for group history storage
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

    def _group_data_key(self, group_id: str) -> str:
        """Get S3 key for group's history file."""
        return f"groups/{group_id}/history.parquet"

    def _group_metadata_key(self, group_id: str) -> str:
        """Get S3 key for group's metadata file."""
        return f"groups/{group_id}/metadata.json"

    def _local_cache_path(self, group_id: str) -> Path:
        """Get local cache path for group's history data."""
        # Sanitize group_id for filesystem (replace slashes)
        safe_id = group_id.replace("/", "_").replace("\\", "_")
        return CACHE_DIR / f"{safe_id}_history.parquet"

    def _is_cache_valid(self, group_id: str, cache_path: Path) -> bool:
        """Check if local cache is valid against S3 metadata.

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
                logger.warning(
                    "No S3 metadata found, invalidating cache",
                    group_id=group_id,
                )
                return False

            # Read cached file row count (metadata only, not full file)
            cached_metadata = pq.read_metadata(cache_path)
            cached_row_count = cached_metadata.num_rows

            # Compare row counts
            if cached_row_count < s3_metadata.row_count:
                logger.info(
                    "Cache stale: S3 has newer data",
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
        """Get metadata for a group's history file.

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
            df: DataFrame with the group's history data

        """
        if df.empty:
            return

        # Get the last record date from the DataFrame
        last_date = pd.to_datetime(df["record_date"]).max()

        metadata = GroupMetadata(
            group_id=group_id,
            last_record_date=last_date.strftime("%Y-%m-%d"),
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
            last_record_date=metadata.last_record_date,
            row_count=metadata.row_count,
        )

    def read_group_history(
        self, group_id: str, *, use_cache: bool = True
    ) -> pd.DataFrame | None:
        """Read historical data for a group.

        Args:
            group_id: Group identifier
            use_cache: If True, use local cache when available (validates against S3 metadata)

        Returns:
            DataFrame with columns: record_date, portfolio_daily_return, selections
            Returns None if not found

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
            with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
                tmp.write(response["Body"].read())
                tmp_path = tmp.name

            df = pd.read_parquet(tmp_path, engine="pyarrow")
            Path(tmp_path).unlink()  # Clean up temp file

            # Update local cache
            if use_cache:
                df.to_parquet(cache_path, index=False, engine="pyarrow")

            logger.info(
                "Read group history from S3",
                group_id=group_id,
                rows=len(df),
            )
            return df

        except self.s3_client.exceptions.NoSuchKey:
            logger.debug("No history found for group", group_id=group_id)
            return None
        except Exception as e:
            logger.error(
                "Failed to read group history",
                group_id=group_id,
                error=str(e),
            )
            return None

    def write_group_history(self, group_id: str, df: pd.DataFrame) -> bool:
        """Write historical data for a group.

        Args:
            group_id: Group identifier
            df: DataFrame with columns: record_date, portfolio_daily_return, selections

        Returns:
            True if successful, False otherwise

        """
        if df.empty:
            logger.warning("Attempted to write empty DataFrame", group_id=group_id)
            return False

        try:
            # Ensure record_date is string format (YYYY-MM-DD)
            if "record_date" not in df.columns:
                logger.error(
                    "DataFrame missing required column: record_date",
                    group_id=group_id,
                )
                return False

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

            tmp_path.unlink()  # Clean up temp file

            # Update metadata
            self._update_metadata(group_id, df)

            # Update local cache
            cache_path = self._local_cache_path(group_id)
            df.to_parquet(cache_path, index=False, engine="pyarrow")

            logger.info(
                "Wrote group history to S3",
                group_id=group_id,
                rows=len(df),
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to write group history",
                group_id=group_id,
                error=str(e),
            )
            return False

    def append_records(
        self,
        group_id: str,
        new_records: pd.DataFrame,
    ) -> bool:
        """Append new records to existing group history.

        Reads existing data, appends new records, deduplicates by record_date,
        and writes back to S3.

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
        existing_df = self.read_group_history(group_id, use_cache=False)

        if existing_df is None or existing_df.empty:
            # No existing data, just write new records
            return self.write_group_history(group_id, new_records)

        # Combine and deduplicate
        combined = pd.concat([existing_df, new_records], ignore_index=True)
        combined = combined.drop_duplicates(subset=["record_date"], keep="last")
        combined = combined.sort_values("record_date").reset_index(drop=True)

        logger.info(
            "Appending records to group history",
            group_id=group_id,
            existing_rows=len(existing_df),
            new_rows=len(new_records),
            total_rows=len(combined),
        )

        return self.write_group_history(group_id, combined)
