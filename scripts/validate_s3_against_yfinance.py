"""Business Unit: data | Status: current.

Validate S3 market data against yfinance adjusted prices.

This script validates that S3 datalake prices match yfinance adjusted prices
(accounting for stock splits, dividends, etc.). Volume is ignored as it varies
between data sources and is not used for indicator calculations.

The goal is to ensure our data "broadly represents the true-ish adjusted price"
for each symbol on each date, which is essential for backtesting and indicators.

Key findings this script can detect:
- Missing dates in S3 (gaps in data)
- Split-affected data (S3 has unadjusted prices, needs re-download)
- Genuine data errors (prices don't match even accounting for splits)

Run locally (yfinance blocks Lambda IP ranges):
    python scripts/validate_s3_against_yfinance.py [--symbols AAPL,MSFT] [--output report.csv]
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import os
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

import boto3
import pandas as pd
import yfinance as yf
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Common split factors to detect (forward and reverse splits)
COMMON_SPLIT_FACTORS = [2, 3, 4, 5, 7, 8, 10, 20, 1 / 2, 1 / 3, 1 / 4, 1 / 5, 1 / 10]


def detect_split_factor(s3_price: float, yf_price: float, tolerance: float = 0.02) -> float | None:
    """Detect if prices differ by a common split factor.

    Args:
        s3_price: Price from S3 (potentially unadjusted)
        yf_price: Price from yfinance (adjusted)
        tolerance: Relative tolerance for matching

    Returns:
        Split factor if detected, None otherwise
    """
    if yf_price == 0 or s3_price == 0:
        return None

    ratio = s3_price / yf_price

    for factor in COMMON_SPLIT_FACTORS:
        if abs(ratio - factor) / factor < tolerance:
            return factor

    return None


@dataclass(frozen=True)
class DataPoint:
    """A single OHLC data point (volume ignored for validation)."""

    date: str  # YYYY-MM-DD
    open_price: float
    high_price: float
    low_price: float
    close_price: float

    def __hash__(self) -> int:
        """Make hashable for set operations."""
        return hash((self.date, self.close_price))

    def prices_match(self, other: "DataPoint", tolerance: float = 0.02) -> bool:
        """Check if prices match within tolerance (absolute, not percentage)."""
        return (
            self.date == other.date
            and abs(self.open_price - other.open_price) < tolerance
            and abs(self.high_price - other.high_price) < tolerance
            and abs(self.low_price - other.low_price) < tolerance
            and abs(self.close_price - other.close_price) < tolerance
        )

    def prices_match_pct(self, other: "DataPoint", tolerance_pct: float = 0.01) -> bool:
        """Check if prices match within percentage tolerance (better for varying price ranges)."""
        if self.date != other.date:
            return False

        def pct_diff(a: float, b: float) -> float:
            if max(abs(a), abs(b)) == 0:
                return 0
            return abs(a - b) / max(abs(a), abs(b))

        return (
            pct_diff(self.open_price, other.open_price) < tolerance_pct
            and pct_diff(self.high_price, other.high_price) < tolerance_pct
            and pct_diff(self.low_price, other.low_price) < tolerance_pct
            and pct_diff(self.close_price, other.close_price) < tolerance_pct
        )

    def detect_split_factor(self, other: "DataPoint") -> float | None:
        """Detect if this point differs from other by a split factor."""
        return detect_split_factor(self.close_price, other.close_price)

    def __eq__(self, other: object) -> bool:
        """Check equality using percentage-based tolerance (1%)."""
        if not isinstance(other, DataPoint):
            return NotImplemented
        return self.prices_match_pct(other, tolerance_pct=0.01)


@dataclass
class SymbolValidationResult:
    """Result of validating a symbol against yfinance adjusted prices."""

    symbol: str
    s3_record_count: int
    yfinance_record_count: int
    s3_start_date: str = ""  # Earliest date in S3
    s3_end_date: str = ""  # Latest date in S3
    missing_in_s3: list[DataPoint] = field(default_factory=list)
    missing_in_yfinance: list[DataPoint] = field(default_factory=list)
    mismatched_records: list[tuple[DataPoint, DataPoint]] = field(default_factory=list)
    detected_split_factor: float | None = None  # If a consistent split factor is detected
    errors: list[str] = field(default_factory=list)

    @property
    def split_affected_records(self) -> list[tuple[DataPoint, DataPoint, float]]:
        """Records that appear to be affected by a stock split (S3 has unadjusted prices).

        Returns list of (s3_point, yf_point, split_factor) tuples.
        """
        results = []
        for s3_pt, yf_pt in self.mismatched_records:
            factor = s3_pt.detect_split_factor(yf_pt)
            if factor is not None:
                results.append((s3_pt, yf_pt, factor))
        return results

    @property
    def genuine_errors(self) -> list[tuple[DataPoint, DataPoint]]:
        """Records with price differences that can't be explained by splits.

        These are genuine data quality issues that need investigation.
        """
        split_dates = {s3_pt.date for s3_pt, _, _ in self.split_affected_records}
        return [
            (s3_pt, yf_pt)
            for s3_pt, yf_pt in self.mismatched_records
            if s3_pt.date not in split_dates
        ]

    @property
    def missing_in_s3_recent(self) -> list[DataPoint]:
        """Records missing in S3 that are within the S3 date range (unexpected gaps)."""
        if not self.s3_start_date or not self.s3_end_date:
            return []
        return [p for p in self.missing_in_s3 if self.s3_start_date <= p.date <= self.s3_end_date]

    @property
    def missing_in_s3_historical(self) -> list[DataPoint]:
        """Records missing in S3 that are before S3 start date (expected - not seeded)."""
        if not self.s3_start_date:
            return self.missing_in_s3
        return [p for p in self.missing_in_s3 if p.date < self.s3_start_date]

    @property
    def needs_adjustment(self) -> bool:
        """Check if this symbol needs split adjustment (has split-affected records)."""
        return len(self.split_affected_records) > 0

    @property
    def is_valid(self) -> bool:
        """Check if symbol data is valid (no genuine errors or gaps).

        A symbol is valid if:
        - No unexpected gaps (missing within S3 date range)
        - No genuine price errors (excluding split-affected data)
        - No errors

        Note: Split-affected data is flagged separately for correction, not as invalid.
        """
        return not self.missing_in_s3_recent and not self.genuine_errors and not self.errors

    @property
    def discrepancy_count(self) -> int:
        """Total number of actionable discrepancies (genuine errors + gaps)."""
        return len(self.missing_in_s3_recent) + len(self.genuine_errors)

    @property
    def historical_gap_count(self) -> int:
        """Number of expected historical gaps (before S3 start date)."""
        return len(self.missing_in_s3_historical)


def read_s3_data(
    s3_client: "boto3.client",
    bucket: str,
    symbol: str,
) -> pd.DataFrame | None:
    """Read Parquet data for a symbol from S3.

    Args:
        s3_client: Initialized S3 client
        bucket: S3 bucket name
        symbol: Ticker symbol

    Returns:
        DataFrame with OHLCV data, or None if not found

    """
    try:
        key = f"{symbol}/daily.parquet"
        response = s3_client.get_object(Bucket=bucket, Key=key)

        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            tmp.write(response["Body"].read())
            tmp_path = tmp.name

        df = pd.read_parquet(tmp_path, engine="pyarrow")
        Path(tmp_path).unlink()

        logger.info(f"Read {len(df)} records from S3 for {symbol}")
        return df

    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            logger.warning(f"No data found in S3 for {symbol}")
            return None
        raise
    except Exception as e:
        logger.error(f"Error reading S3 data for {symbol}: {e}")
        return None


def fetch_yfinance_data(
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
    max_retries: int = 3,
) -> pd.DataFrame | None:
    """Fetch historical data from yfinance.

    Args:
        symbol: Ticker symbol
        start_date: Optional start date (YYYY-MM-DD) to limit fetch range
        end_date: Optional end date (YYYY-MM-DD) to limit fetch range
        max_retries: Number of retries on failure

    Returns:
        DataFrame with OHLCV data, or None if fetch fails

    """
    import warnings

    # Suppress yfinance FutureWarning about auto_adjust default
    warnings.filterwarnings("ignore", message=".*auto_adjust default to True.*")

    for attempt in range(max_retries):
        try:
            # Use date range if provided, otherwise fetch max history
            if start_date and end_date:
                # Add 1 day to end_date since yfinance end is exclusive
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                end_str = end_dt.strftime("%Y-%m-%d")
                df = yf.download(
                    symbol,
                    progress=False,
                    start=start_date,
                    end=end_str,
                    auto_adjust=False,
                )
            else:
                df = yf.download(symbol, progress=False, period="max", auto_adjust=False)

            if df is None or df.empty:
                logger.warning(f"Empty data from yfinance for {symbol}")
                return None
            logger.info(f"Fetched {len(df)} records from yfinance for {symbol}")
            return df
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1} failed for {symbol}, retrying: {e}")
            else:
                logger.error(f"Failed to fetch yfinance data for {symbol}: {e}")
                return None
    return None


def normalize_dataframe(df: pd.DataFrame, source: str) -> list[DataPoint]:
    """Normalize a dataframe to a list of DataPoint objects.

    Args:
        df: DataFrame with OHLCV data
        source: Source name for logging (e.g., "S3", "yfinance")

    Returns:
        List of DataPoint objects

    """
    if df is None or df.empty:
        return []

    points: list[DataPoint] = []

    # Handle yfinance MultiIndex columns (tuples) by flattening to single level
    if isinstance(df.columns, pd.MultiIndex):
        # Flatten MultiIndex: take first level only (the OHLCV names)
        df.columns = df.columns.get_level_values(0)

    # Create lowercase mapping for case-insensitive column lookup
    columns_lower: dict[str, str] = {}
    for col in df.columns:
        # Handle both string and non-string column names
        col_str = str(col)
        columns_lower[col_str.lower()] = col

    # Determine date column/index
    # S3 data uses 'timestamp' column, yfinance uses DatetimeIndex
    has_timestamp_col = "timestamp" in columns_lower
    date_col = columns_lower.get("timestamp") if has_timestamp_col else None

    # Find OHLC columns (volume ignored - only prices matter for indicators)
    # Note: Use regular Close (not Adj Close) for comparison since S3 stores unadjusted prices
    open_col = columns_lower.get("open")
    high_col = columns_lower.get("high")
    low_col = columns_lower.get("low")
    close_col = columns_lower.get("close")  # Prefer Close over Adj Close for S3 compatibility

    # Fallback to pattern matching if not found
    if not open_col:
        open_col = next((c for c in df.columns if "open" in str(c).lower()), None)
    if not high_col:
        high_col = next((c for c in df.columns if "high" in str(c).lower()), None)
    if not low_col:
        low_col = next((c for c in df.columns if "low" in str(c).lower()), None)
    if not close_col:
        # Prefer regular Close over Adj Close for S3 compatibility
        close_col = next(
            (c for c in df.columns if str(c).lower() == "close"),
            next((c for c in df.columns if "close" in str(c).lower()), None),
        )

    for idx, row in df.iterrows():
        try:
            # Parse date - S3 has 'timestamp' column, yfinance uses index
            if has_timestamp_col and date_col:
                date_val = row[date_col]
            else:
                date_val = idx

            # Convert to YYYY-MM-DD string
            if isinstance(date_val, str):
                date_str = date_val[:10]  # Take first 10 chars
            else:
                date_str = pd.to_datetime(date_val).strftime("%Y-%m-%d")

            # Volume is intentionally excluded - we only validate prices
            point = DataPoint(
                date=date_str,
                open_price=float(row.get(open_col, 0)) if open_col else 0.0,
                high_price=float(row.get(high_col, 0)) if high_col else 0.0,
                low_price=float(row.get(low_col, 0)) if low_col else 0.0,
                close_price=float(row.get(close_col, 0)) if close_col else 0.0,
            )
            points.append(point)
        except Exception as e:
            logger.warning(f"Failed to parse row for {idx}: {e}")
            continue

    logger.debug(f"Normalized {len(points)} points from {source}")
    return points


def validate_symbol(
    symbol: str,
    s3_client: "boto3.client",
    bucket: str,
    debug: bool = False,
) -> SymbolValidationResult:
    """Validate a single symbol's data against yfinance.

    Args:
        symbol: Ticker symbol
        s3_client: Initialized S3 client
        bucket: S3 bucket name
        debug: If True, print sample mismatches with actual values

    Returns:
        SymbolValidationResult with discrepancies

    """
    result = SymbolValidationResult(symbol=symbol, s3_record_count=0, yfinance_record_count=0)

    # Fetch S3 data first to determine date range
    s3_df = read_s3_data(s3_client, bucket, symbol)
    if s3_df is None:
        result.errors.append(f"No S3 data found for {symbol}")
        return result

    result.s3_record_count = len(s3_df)

    # Normalize S3 data to get date range
    s3_points = normalize_dataframe(s3_df, "S3")

    # Capture S3 date range
    if s3_points:
        sorted_dates = sorted(p.date for p in s3_points)
        result.s3_start_date = sorted_dates[0]
        result.s3_end_date = sorted_dates[-1]

    # Fetch yfinance data LIMITED to S3 date range (avoid historical data we don't have)
    yf_df = fetch_yfinance_data(
        symbol,
        start_date=result.s3_start_date,
        end_date=result.s3_end_date,
    )
    if yf_df is None:
        result.errors.append(f"Failed to fetch yfinance data for {symbol}")
        return result

    result.yfinance_record_count = len(yf_df)

    # Normalize yfinance data
    yf_points = normalize_dataframe(yf_df, "yfinance")

    # Convert to dicts for comparison (by date)
    s3_by_date = {p.date: p for p in s3_points}
    yf_by_date = {p.date: p for p in yf_points}

    # Find missing dates
    s3_dates = set(s3_by_date.keys())
    yf_dates = set(yf_by_date.keys())

    for date in yf_dates - s3_dates:
        result.missing_in_s3.append(yf_by_date[date])

    for date in s3_dates - yf_dates:
        result.missing_in_yfinance.append(s3_by_date[date])

    # Check for mismatches in overlapping dates
    for date in s3_dates & yf_dates:
        s3_point = s3_by_date[date]
        yf_point = yf_by_date[date]
        if s3_point != yf_point:
            result.mismatched_records.append((s3_point, yf_point))

    # Debug: print sample mismatches with actual values
    if debug and result.mismatched_records:
        split_count = len(result.split_affected_records)
        genuine_count = len(result.genuine_errors)
        print(f"\n=== DEBUG: Mismatch breakdown for {symbol} ===")
        print(f"  Total price mismatches: {len(result.mismatched_records)}")
        print(f"    - Split-adjusted (can be fixed): {split_count}")
        print(f"    - Genuine errors: {genuine_count}")

        if result.mismatched_records:
            print(f"\n  Sample PRICE mismatches:")
            for i, (s3_pt, yf_pt) in enumerate(result.mismatched_records[:3]):
                print(f"    [{i + 1}] Date: {s3_pt.date}")
                print(
                    f"        S3:  O={s3_pt.open_price:.4f} H={s3_pt.high_price:.4f} L={s3_pt.low_price:.4f} C={s3_pt.close_price:.4f}"
                )
                print(
                    f"        YF:  O={yf_pt.open_price:.4f} H={yf_pt.high_price:.4f} L={yf_pt.low_price:.4f} C={yf_pt.close_price:.4f}"
                )
                # Check for split factor
                if yf_pt.close_price > 0:
                    ratio = s3_pt.close_price / yf_pt.close_price
                    if 1.9 < ratio < 2.1 or 0.48 < ratio < 0.52:
                        print(f"        ⚠️  Likely split-adjusted (ratio: {ratio:.2f}x)")

    logger.info(
        f"Validation complete for {symbol}: "
        f"S3={result.s3_record_count} ({result.s3_start_date} to {result.s3_end_date}), "
        f"yfinance={result.yfinance_record_count}, "
        f"gaps={len(result.missing_in_s3_recent)} unexpected, "
        f"mismatches={len(result.mismatched_records)} (split={len(result.split_affected_records)}, genuine={len(result.genuine_errors)})"
    )

    return result


def list_s3_symbols(s3_client: "boto3.client", bucket: str) -> list[str]:
    """List all symbols available in S3.

    Args:
        s3_client: Initialized S3 client
        bucket: S3 bucket name

    Returns:
        List of symbol names

    """
    symbols: set[str] = set()
    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket, Delimiter="/")

    for page in pages:
        if "CommonPrefixes" in page:
            for prefix in page["CommonPrefixes"]:
                symbol = prefix["Prefix"].rstrip("/")
                if symbol:
                    symbols.add(symbol)

    return sorted(symbols)


def write_csv_report(results: list[SymbolValidationResult], output_file: str) -> None:
    """Write validation results to CSV report.

    Args:
        results: List of SymbolValidationResult objects
        output_file: Path to output CSV file

    """
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)

        # Write summary header
        writer.writerow(["VALIDATION REPORT", datetime.now(UTC).isoformat()])
        writer.writerow([])

        # Summary stats
        total_symbols = len(results)
        valid_symbols = sum(1 for r in results if r.is_valid)
        writer.writerow(["Total Symbols", total_symbols])
        writer.writerow(["Valid Symbols", valid_symbols])
        writer.writerow(["Invalid Symbols", total_symbols - valid_symbols])
        writer.writerow([])

        # Symbol details header
        writer.writerow(
            [
                "Symbol",
                "S3 Records",
                "S3 Date Range",
                "yfinance Records",
                "Historical Gaps",
                "Unexpected Gaps",
                "Missing in yfinance",
                "Mismatched",
                "Errors",
                "Status",
            ]
        )

        for result in results:
            date_range = (
                f"{result.s3_start_date} to {result.s3_end_date}" if result.s3_start_date else "N/A"
            )
            writer.writerow(
                [
                    result.symbol,
                    result.s3_record_count,
                    date_range,
                    result.yfinance_record_count,
                    result.historical_gap_count,
                    len(result.missing_in_s3_recent),
                    len(result.missing_in_yfinance),
                    len(result.mismatched_records),
                    "; ".join(result.errors) if result.errors else "",
                    "VALID" if result.is_valid else "INVALID",
                ]
            )

    logger.info(f"Report written to {output_file}")


def write_detailed_report(results: list[SymbolValidationResult], output_file: str) -> None:
    """Write detailed discrepancies to JSON file.

    Args:
        results: List of SymbolValidationResult objects
        output_file: Path to output JSON file

    """
    report: dict[str, dict] = {}

    for result in results:
        if not result.is_valid or result.historical_gap_count > 0:
            symbol_report: dict = {
                "s3_record_count": result.s3_record_count,
                "yfinance_record_count": result.yfinance_record_count,
                "s3_date_range": f"{result.s3_start_date} to {result.s3_end_date}"
                if result.s3_start_date
                else "N/A",
                "historical_gaps": result.historical_gap_count,
                "unexpected_gaps": len(result.missing_in_s3_recent),
                "is_valid": result.is_valid,
                "errors": result.errors,
            }

            # Only include unexpected gaps in detail (not historical)
            if result.missing_in_s3_recent:
                symbol_report["unexpected_gaps_detail"] = [
                    {
                        "date": p.date,
                        "close": p.close_price,
                    }
                    for p in result.missing_in_s3_recent[:20]  # Limit to 20
                ]

            if result.missing_in_yfinance:
                symbol_report["missing_in_yfinance"] = [
                    {
                        "date": p.date,
                        "close": p.close_price,
                    }
                    for p in result.missing_in_yfinance
                ]

            if result.mismatched_records:
                symbol_report["mismatched"] = [
                    {
                        "date": s3_point.date,
                        "s3_close": s3_point.close_price,
                        "yf_close": yf_point.close_price,
                        "ratio": round(s3_point.close_price / yf_point.close_price, 4)
                        if yf_point.close_price
                        else None,
                    }
                    for s3_point, yf_point in result.mismatched_records[:10]  # Limit to 10
                ]

            report[result.symbol] = symbol_report

    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Detailed report written to {output_file}")


def discover_markers_table_from_cloudformation(region: str) -> str | None:
    """Attempt to discover bad data markers table from CloudFormation.

    Args:
        region: AWS region

    Returns:
        Table name if found, None otherwise

    """
    try:
        cf_client = boto3.client("cloudformation", region_name=region)

        # Try common stack names in order of likelihood
        stack_names = [
            "alchemiser-dev",
            "alchemiser-staging",
            "alchemiser-prod",
        ]

        for stack_name in stack_names:
            try:
                response = cf_client.describe_stacks(StackName=stack_name)
                if response["Stacks"]:
                    # Table name follows pattern: alchemiser-{stage}-bad-data-markers
                    stage = stack_name.replace("alchemiser-", "")
                    table_name = f"alchemiser-{stage}-bad-data-markers"
                    logger.info(f"Inferred markers table from stack {stack_name}: {table_name}")
                    return table_name
            except cf_client.exceptions.ClientError as e:
                if e.response["Error"]["Code"] != "ValidationError":
                    raise
                continue

    except Exception as e:
        logger.warning(f"Failed to discover markers table: {e}")

    return None


def write_bad_data_markers(
    results: list[SymbolValidationResult],
    region: str,
) -> int:
    """Write bad data markers to DynamoDB for symbols needing re-fetch.

    Args:
        results: Validation results
        region: AWS region

    Returns:
        Number of markers written

    """
    # Discover table name
    table_name = discover_markers_table_from_cloudformation(region)

    if not table_name:
        logger.error("Could not discover markers table. Ensure alchemiser stack is deployed.")
        return 0

    # Import the service (local import to avoid circular deps)
    # We're adding the project to path so we can import from the_alchemiser
    import sys
    from pathlib import Path

    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from the_alchemiser.data_v2.bad_data_marker_service import BadDataMarkerService

    marker_service = BadDataMarkerService(table_name=table_name)

    markers_written = 0

    for result in results:
        # Only mark symbols with split-affected records
        if not result.split_affected_records:
            continue

        # Get representative split factor
        split_factors = [factor for _, _, factor in result.split_affected_records]
        avg_factor = sum(split_factors) / len(split_factors) if split_factors else None

        success = marker_service.mark_symbol_for_refetch(
            symbol=result.symbol,
            reason="split_adjusted",
            start_date=result.s3_start_date,
            end_date=result.s3_end_date,
            detected_ratio=avg_factor,
            source="validation_script",
        )

        if success:
            markers_written += 1
            logger.info(
                f"Marked {result.symbol} for re-fetch "
                f"({len(result.split_affected_records)} split-affected records, "
                f"ratio: {avg_factor:.2f}x)"
            )

    return markers_written


def discover_bucket_from_cloudformation(region: str) -> str | None:
    """Attempt to discover bucket from CloudFormation stack outputs.

    Looks for stack outputs named MarketDataBucketName in stacks matching:
    - alchemiser-dev (dev stage)
    - alchemiser-staging (staging stage)
    - alchemiser-prod (prod stage)

    Args:
        region: AWS region

    Returns:
        Bucket name if found, None otherwise

    """
    try:
        cf_client = boto3.client("cloudformation", region_name=region)

        # Try common stack names in order of likelihood
        stack_names = [
            "alchemiser-dev",
            "alchemiser-staging",
            "alchemiser-prod",
        ]

        for stack_name in stack_names:
            try:
                response = cf_client.describe_stacks(StackName=stack_name)
                if response["Stacks"]:
                    stack = response["Stacks"][0]
                    if "Outputs" in stack:
                        for output in stack["Outputs"]:
                            if output.get("OutputKey") == "MarketDataBucketName":
                                bucket = output.get("OutputValue")
                                logger.info(
                                    f"Auto-discovered bucket from CloudFormation stack {stack_name}: {bucket}"
                                )
                                return bucket
            except cf_client.exceptions.ClientError as e:
                if e.response["Error"]["Code"] != "ValidationError":
                    raise
                # Stack doesn't exist, try next one
                continue

    except Exception as e:
        logger.warning(f"Failed to auto-discover bucket from CloudFormation: {e}")

    return None


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate S3 market data against yfinance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate all symbols (auto-discovers bucket from CloudFormation)
  python scripts/validate_s3_against_yfinance.py

  # Validate specific symbols
  python scripts/validate_s3_against_yfinance.py --symbols AAPL,MSFT,GOOGL

  # Limit to first 10 symbols
  python scripts/validate_s3_against_yfinance.py --limit 10

  # Custom output file
  python scripts/validate_s3_against_yfinance.py --output validation_report.csv

  # Explicit bucket (overrides auto-discovery)
  python scripts/validate_s3_against_yfinance.py --bucket my-bucket
        """,
    )
    parser.add_argument(
        "--symbols",
        type=str,
        help="Comma-separated list of symbols to validate (default: all)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of symbols to validate",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="s3_validation_report.csv",
        help="Output CSV report file (default: s3_validation_report.csv)",
    )
    parser.add_argument(
        "--detailed",
        type=str,
        help="Output detailed JSON report of discrepancies",
    )
    parser.add_argument(
        "--bucket",
        type=str,
        default=None,
        help="S3 bucket name (default: auto-discover from CloudFormation, MARKET_DATA_BUCKET env var, or specify explicitly)",
    )
    parser.add_argument(
        "--region",
        type=str,
        default="us-east-1",
        help="AWS region (default: us-east-1)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print sample mismatches with actual S3 vs yfinance values for debugging",
    )
    parser.add_argument(
        "--mark-bad",
        action="store_true",
        help="Write bad data markers to DynamoDB for symbols with split-adjusted data. "
        "These markers will be processed by the next Data Lambda run to re-fetch data.",
    )

    args = parser.parse_args()

    # Resolve bucket: explicit arg > env var > CloudFormation auto-discovery
    bucket = args.bucket or os.environ.get("MARKET_DATA_BUCKET")

    if not bucket:
        logger.info("Attempting to auto-discover bucket from CloudFormation...")
        bucket = discover_bucket_from_cloudformation(args.region)

    if not bucket:
        logger.error(
            "Bucket not found. Provide via:\n"
            "  1. --bucket argument\n"
            "  2. MARKET_DATA_BUCKET env var\n"
            "  3. CloudFormation stack output (auto-discovered from alchemiser-dev/staging/prod stacks)"
        )
        sys.exit(1)

    logger.info(f"Using bucket: {bucket}")

    # Initialize S3 client
    s3_client = boto3.client("s3", region_name=args.region)

    # Determine symbols to validate
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",")]
    else:
        logger.info("Listing symbols from S3...")
        symbols = list_s3_symbols(s3_client, bucket)
        logger.info(f"Found {len(symbols)} symbols in S3")

    if args.limit:
        symbols = symbols[: args.limit]
        logger.info(f"Limiting to first {args.limit} symbols")

    # Validate each symbol
    results: list[SymbolValidationResult] = []
    for i, symbol in enumerate(symbols, 1):
        logger.info(f"[{i}/{len(symbols)}] Validating {symbol}...")
        try:
            result = validate_symbol(symbol, s3_client, bucket, debug=args.debug)
            results.append(result)
        except Exception as e:
            logger.error(f"Unexpected error validating {symbol}: {e}")
            result = SymbolValidationResult(
                symbol=symbol,
                s3_record_count=0,
                yfinance_record_count=0,
                errors=[str(e)],
            )
            results.append(result)

    # Write reports
    write_csv_report(results, args.output)

    if args.detailed:
        write_detailed_report(results, args.detailed)

    # Write bad data markers if requested
    markers_written = 0
    if args.mark_bad:
        symbols_with_splits = [r for r in results if r.split_affected_records]
        if symbols_with_splits:
            print(
                f"\nWriting bad data markers for {len(symbols_with_splits)} symbols with split-affected data..."
            )
            markers_written = write_bad_data_markers(results, args.region)
            print(f"✅ Wrote {markers_written} markers to DynamoDB")
            print("   These will be processed on next Data Lambda run.")
        else:
            print("\nNo symbols with split-affected data found - no markers to write.")

    # Print summary
    valid_count = sum(1 for r in results if r.is_valid)
    invalid_count = len(results) - valid_count
    total_mismatches = sum(len(r.mismatched_records) for r in results)
    total_split_affected = sum(len(r.split_affected_records) for r in results)
    total_genuine_errors = sum(len(r.genuine_errors) for r in results)
    total_unexpected_gaps = sum(len(r.missing_in_s3_recent) for r in results)

    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total Symbols Validated: {len(results)}")
    print(f"Valid Symbols: {valid_count}")
    print(f"Invalid Symbols: {invalid_count}")
    print()
    print("Discrepancy Breakdown:")
    print(f"  - Unexpected gaps (missing dates in S3): {total_unexpected_gaps}")
    print(f"  - Total price mismatches: {total_mismatches}")
    print(
        f"    - Split-adjusted (fixable by re-fetching with adjustment='all'): {total_split_affected}"
    )
    print(f"    - Genuine errors (unexplained): {total_genuine_errors}")
    print()
    print(f"Report: {args.output}")
    if args.detailed:
        print(f"Detailed Report: {args.detailed}")
    if markers_written > 0:
        print(f"Bad Data Markers Written: {markers_written}")
    print("=" * 80)

    if invalid_count > 0:
        print("\nInvalid Symbols (genuine errors or gaps):")
        for result in results:
            if not result.is_valid:
                print(
                    f"  - {result.symbol} ({result.s3_start_date} to {result.s3_end_date}): "
                    f"{len(result.missing_in_s3_recent)} gaps, "
                    f"{len(result.genuine_errors)} genuine errors"
                )

    # Note about split-adjusted data
    if total_split_affected > 0:
        print(f"\n⚠️  NOTE: {total_split_affected} records have split-adjusted price differences.")
        print(
            "   yfinance returns split-adjusted prices, while Alpaca/S3 stores unadjusted prices."
        )
        if markers_written > 0:
            print(
                f"   ✅ {markers_written} symbols marked for re-fetch - will be processed on next Data Lambda run."
            )
        else:
            print("   Run with --mark-bad to write DynamoDB markers for automatic re-fetch.")


if __name__ == "__main__":
    main()
