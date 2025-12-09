"""Business Unit: data | Status: current.

Market data store for S3 Parquet files.

Handles reading, writing, and incremental updates of historical market data
stored as Parquet files in S3. Each symbol has its own Parquet file containing
all available daily bars.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

import boto3
import pandas as pd

from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

logger = get_logger(__name__)

# Module constant for cache directory
CACHE_DIR = Path(tempfile.gettempdir()) / "alchemiser_market_data"


@dataclass(frozen=True)
class SymbolMetadata:
    """Metadata for a symbol's data file in S3.

    Attributes:
        symbol: Ticker symbol
        last_bar_date: Date of the most recent bar in the file
        row_count: Total number of bars in the file
        updated_at: When the metadata was last updated

    """

    symbol: str
    last_bar_date: str  # YYYY-MM-DD format
    row_count: int
    updated_at: str  # ISO format timestamp

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "symbol": self.symbol,
            "last_bar_date": self.last_bar_date,
            "row_count": self.row_count,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SymbolMetadata:
        """Create from dictionary."""
        return cls(
            symbol=data["symbol"],
            last_bar_date=data["last_bar_date"],
            row_count=data["row_count"],
            updated_at=data["updated_at"],
        )


class MarketDataStore:
    """S3-backed store for historical market data in Parquet format.

    Provides read/write access to symbol data with incremental update support.
    Data is organized as: s3://{bucket}/{symbol}/daily.parquet

    Attributes:
        bucket_name: S3 bucket name for market data storage
        region: AWS region for S3 client

    """

    def __init__(
        self,
        bucket_name: str | None = None,
        region: str = "us-east-1",
        s3_client: S3Client | None = None,
    ) -> None:
        """Initialize market data store.

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
            "MarketDataStore initialized",
            bucket=self.bucket_name,
            region=self.region,
        )

    @property
    def s3_client(self) -> S3Client:
        """Lazy-initialized S3 client."""
        if self._s3_client is None:
            self._s3_client = boto3.client("s3", region_name=self.region)
        return self._s3_client

    def _symbol_data_key(self, symbol: str) -> str:
        """Get S3 key for symbol's data file."""
        return f"{symbol}/daily.parquet"

    def _symbol_metadata_key(self, symbol: str) -> str:
        """Get S3 key for symbol's metadata file."""
        return f"{symbol}/metadata.json"

    def _local_cache_path(self, symbol: str) -> Path:
        """Get local cache path for symbol's data."""
        return CACHE_DIR / f"{symbol}_daily.parquet"

    def get_metadata(self, symbol: str) -> SymbolMetadata | None:
        """Get metadata for a symbol's data file.

        Args:
            symbol: Ticker symbol

        Returns:
            SymbolMetadata if file exists, None otherwise

        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=self._symbol_metadata_key(symbol),
            )
            data = json.loads(response["Body"].read().decode("utf-8"))
            return SymbolMetadata.from_dict(data)
        except self.s3_client.exceptions.NoSuchKey:
            return None
        except Exception as e:
            logger.warning(
                "Failed to get metadata",
                symbol=symbol,
                error=str(e),
            )
            return None

    def _update_metadata(self, symbol: str, df: pd.DataFrame) -> None:
        """Update metadata file for symbol after data update.

        Args:
            symbol: Ticker symbol
            df: DataFrame with the symbol's data

        """
        if df.empty:
            return

        # Get the last bar date from the DataFrame
        if "timestamp" in df.columns:
            last_date = pd.to_datetime(df["timestamp"]).max()
        else:
            # Assume index is datetime
            last_date = df.index.max()

        metadata = SymbolMetadata(
            symbol=symbol,
            last_bar_date=last_date.strftime("%Y-%m-%d"),
            row_count=len(df),
            updated_at=datetime.now(UTC).isoformat(),
        )

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=self._symbol_metadata_key(symbol),
            Body=json.dumps(metadata.to_dict()).encode("utf-8"),
            ContentType="application/json",
        )

        logger.debug(
            "Updated metadata",
            symbol=symbol,
            last_bar_date=metadata.last_bar_date,
            row_count=metadata.row_count,
        )

    def read_symbol_data(self, symbol: str, *, use_cache: bool = True) -> pd.DataFrame | None:
        """Read historical data for a symbol.

        Args:
            symbol: Ticker symbol
            use_cache: If True, use local cache when available

        Returns:
            DataFrame with OHLCV data, or None if not found

        """
        cache_path = self._local_cache_path(symbol)

        # Check local cache first
        if use_cache and cache_path.exists():
            try:
                df = pd.read_parquet(cache_path, engine="fastparquet")
                logger.debug(
                    "Read from cache",
                    symbol=symbol,
                    rows=len(df),
                )
                return df
            except Exception as e:
                logger.warning(
                    "Cache read failed, fetching from S3",
                    symbol=symbol,
                    error=str(e),
                )

        # Fetch from S3
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=self._symbol_data_key(symbol),
            )

            # Write to temp file for pandas to read
            with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
                tmp.write(response["Body"].read())
                tmp_path = tmp.name

            df = pd.read_parquet(tmp_path, engine="fastparquet")
            Path(tmp_path).unlink()  # Clean up temp file

            # Update local cache
            if use_cache:
                df.to_parquet(cache_path, index=False, engine="fastparquet")

            logger.info(
                "Read from S3",
                symbol=symbol,
                rows=len(df),
            )
            return df

        except self.s3_client.exceptions.NoSuchKey:
            logger.debug("No data found for symbol", symbol=symbol)
            return None
        except Exception as e:
            logger.error(
                "Failed to read symbol data",
                symbol=symbol,
                error=str(e),
            )
            return None

    def write_symbol_data(self, symbol: str, df: pd.DataFrame) -> bool:
        """Write historical data for a symbol.

        Args:
            symbol: Ticker symbol
            df: DataFrame with OHLCV data

        Returns:
            True if successful, False otherwise

        """
        if df.empty:
            logger.warning("Attempted to write empty DataFrame", symbol=symbol)
            return False

        try:
            # Write to temp file first
            with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
                df.to_parquet(tmp.name, index=False, compression="snappy", engine="fastparquet")
                tmp_path = Path(tmp.name)

            # Upload to S3
            with tmp_path.open("rb") as f:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=self._symbol_data_key(symbol),
                    Body=f.read(),
                    ContentType="application/octet-stream",
                )

            tmp_path.unlink()  # Clean up temp file

            # Update metadata
            self._update_metadata(symbol, df)

            # Update local cache
            cache_path = self._local_cache_path(symbol)
            df.to_parquet(cache_path, index=False, engine="fastparquet")

            logger.info(
                "Wrote symbol data to S3",
                symbol=symbol,
                rows=len(df),
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to write symbol data",
                symbol=symbol,
                error=str(e),
            )
            return False

    def append_bars(self, symbol: str, new_bars: pd.DataFrame) -> bool:
        """Append new bars to existing symbol data.

        Handles deduplication by timestamp to ensure idempotent updates.

        Args:
            symbol: Ticker symbol
            new_bars: DataFrame with new OHLCV bars to append

        Returns:
            True if successful, False otherwise

        """
        if new_bars.empty:
            logger.debug("No new bars to append", symbol=symbol)
            return True

        # Read existing data
        existing_df = self.read_symbol_data(symbol, use_cache=False)

        if existing_df is None:
            # No existing data, write new bars directly
            return self.write_symbol_data(symbol, new_bars)

        # Ensure timestamp column exists in both
        if "timestamp" not in existing_df.columns or "timestamp" not in new_bars.columns:
            logger.error(
                "Missing timestamp column for deduplication",
                symbol=symbol,
            )
            return False

        # Convert timestamps for comparison
        existing_df["timestamp"] = pd.to_datetime(existing_df["timestamp"])
        new_bars["timestamp"] = pd.to_datetime(new_bars["timestamp"])

        # Filter out bars that already exist
        existing_dates = set(existing_df["timestamp"].dt.date)
        new_bars_filtered = new_bars[~new_bars["timestamp"].dt.date.isin(existing_dates)]

        if new_bars_filtered.empty:
            logger.debug("All bars already exist", symbol=symbol)
            return True

        # Concatenate and sort by timestamp
        combined_df = pd.concat([existing_df, new_bars_filtered], ignore_index=True)
        combined_df = combined_df.sort_values("timestamp").reset_index(drop=True)

        logger.info(
            "Appending bars",
            symbol=symbol,
            existing_rows=len(existing_df),
            new_rows=len(new_bars_filtered),
            total_rows=len(combined_df),
        )

        return self.write_symbol_data(symbol, combined_df)

    def download_to_cache(self, symbols: list[str]) -> dict[str, bool]:
        """Download multiple symbols to local cache.

        Args:
            symbols: List of ticker symbols to download

        Returns:
            Dict mapping symbol to success status

        """
        results: dict[str, bool] = {}

        for symbol in symbols:
            df = self.read_symbol_data(symbol, use_cache=False)
            results[symbol] = df is not None

        logger.info(
            "Downloaded symbols to cache",
            total=len(symbols),
            success=sum(results.values()),
            failed=len(symbols) - sum(results.values()),
        )

        return results

    def list_symbols(self) -> list[str]:
        """List all symbols that have data in S3.

        Returns:
            List of ticker symbols with data files

        """
        symbols: list[str] = []
        paginator = self.s3_client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=self.bucket_name, Delimiter="/"):
            for prefix in page.get("CommonPrefixes", []):
                # Extract symbol from prefix like "AAPL/"
                symbol = prefix["Prefix"].rstrip("/")
                symbols.append(symbol)

        logger.debug("Listed symbols", count=len(symbols))
        return sorted(symbols)

    def get_bars_for_indicator(
        self,
        symbol: str,
        lookback_days: int = 365,
    ) -> pd.Series | None:
        """Get closing prices for indicator computation.

        Convenience method that returns just the close prices as a Series,
        suitable for passing to technical indicator functions.

        Args:
            symbol: Ticker symbol
            lookback_days: Number of days of data to return

        Returns:
            Series of closing prices indexed by date, or None if not found

        """
        df = self.read_symbol_data(symbol)
        if df is None or df.empty:
            return None

        # Ensure timestamp column and sort
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")
        else:
            return None

        # Filter to lookback period
        cutoff_date = datetime.now(UTC) - timedelta(days=lookback_days)
        df = df[df["timestamp"] >= cutoff_date]

        if df.empty:
            return None

        # Return close prices as Series
        return pd.Series(df["close"].values, index=df["timestamp"])
