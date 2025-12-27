"""Business Unit: data_quality_monitor | Status: current.

Data quality validation logic.

Compares S3 parquet market data against external data sources (Yahoo Finance)
to detect data quality issues.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pandas as pd
import yfinance as yf

from the_alchemiser.data_v2.market_data_store import MarketDataStore
from the_alchemiser.data_v2.symbol_extractor import SymbolExtractor
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of data quality validation for a symbol."""

    symbol: str
    passed: bool
    issues: list[str]
    rows_checked: int
    external_source: str


class DataQualityChecker:
    """Validates market data quality by comparing against external sources."""

    def __init__(self) -> None:
        """Initialize quality checker with S3 access."""
        bucket = os.environ.get("MARKET_DATA_BUCKET", "alchemiser-shared-market-data")
        self.market_data_store = MarketDataStore(bucket)
        self.symbol_extractor = SymbolExtractor()

    def validate_all_symbols(
        self,
        lookback_days: int = 5,
    ) -> dict[str, ValidationResult]:
        """Validate all symbols from strategy configs.

        Args:
            lookback_days: Number of recent days to validate

        Returns:
            Dict mapping symbol to validation result

        """
        # Extract all symbols from strategy configs
        symbols = self.symbol_extractor.extract_all_symbols()

        logger.info(
            "Validating all symbols",
            extra={
                "total_symbols": len(symbols),
                "lookback_days": lookback_days,
            },
        )

        return self.validate_symbols(symbols, lookback_days)

    def validate_symbols(
        self,
        symbols: list[str],
        lookback_days: int = 5,
    ) -> dict[str, ValidationResult]:
        """Validate specific symbols.

        Args:
            symbols: List of symbols to validate
            lookback_days: Number of recent days to validate

        Returns:
            Dict mapping symbol to validation result

        """
        results = {}

        for symbol in symbols:
            try:
                result = self._validate_symbol(symbol, lookback_days)
                results[symbol] = result
            except Exception as e:
                logger.error(
                    "Failed to validate symbol",
                    extra={"symbol": symbol, "error": str(e)},
                    exc_info=True,
                )
                results[symbol] = ValidationResult(
                    symbol=symbol,
                    passed=False,
                    issues=[f"Validation failed: {e}"],
                    rows_checked=0,
                    external_source="yfinance",
                )

        return results

    def _validate_symbol(
        self,
        symbol: str,
        lookback_days: int,
    ) -> ValidationResult:
        """Validate a single symbol.

        Args:
            symbol: Symbol to validate
            lookback_days: Number of recent days to validate

        Returns:
            Validation result

        """
        issues: list[str] = []

        # Fetch our S3 data
        our_data = self._fetch_our_data(symbol, lookback_days)

        if our_data is None or our_data.empty:
            issues.append("No data found in S3")
            return ValidationResult(
                symbol=symbol,
                passed=False,
                issues=issues,
                rows_checked=0,
                external_source="yfinance",
            )

        # Fetch external data for comparison
        external_data = self._fetch_external_data(symbol, lookback_days)

        if external_data is None or external_data.empty:
            issues.append("No external data available for comparison")
            return ValidationResult(
                symbol=symbol,
                passed=False,
                issues=issues,
                rows_checked=len(our_data),
                external_source="yfinance",
            )

        # Validate data freshness
        freshness_issues = self._check_freshness(our_data)
        issues.extend(freshness_issues)

        # Validate data completeness (missing dates)
        completeness_issues = self._check_completeness(our_data, external_data)
        issues.extend(completeness_issues)

        # Validate price accuracy (within tolerance)
        accuracy_issues = self._check_price_accuracy(our_data, external_data)
        issues.extend(accuracy_issues)

        passed = len(issues) == 0

        return ValidationResult(
            symbol=symbol,
            passed=passed,
            issues=issues,
            rows_checked=len(our_data),
            external_source="yfinance",
        )

    def _fetch_our_data(
        self,
        symbol: str,
        lookback_days: int,
    ) -> pd.DataFrame | None:
        """Fetch our data from S3.

        Args:
            symbol: Symbol to fetch
            lookback_days: Number of days to fetch

        Returns:
            DataFrame with our data, or None if not found

        """
        try:
            # Calculate date range
            end_date = datetime.now(UTC).date()
            start_date = end_date - timedelta(days=lookback_days)

            # Fetch from S3
            df = self.market_data_store.read_bars(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )

            return df

        except Exception as e:
            logger.warning(
                "Failed to fetch our data",
                extra={"symbol": symbol, "error": str(e)},
            )
            return None

    def _fetch_external_data(
        self,
        symbol: str,
        lookback_days: int,
    ) -> pd.DataFrame | None:
        """Fetch external data from Yahoo Finance.

        Args:
            symbol: Symbol to fetch
            lookback_days: Number of days to fetch

        Returns:
            DataFrame with external data, or None if not found

        """
        try:
            # Fetch from Yahoo Finance
            ticker = yf.Ticker(symbol)

            # Get data for the lookback period
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=lookback_days + 5)  # Buffer for weekends

            df = ticker.history(
                start=start_date,
                end=end_date,
                interval="1d",
                auto_adjust=True,
            )

            if df.empty:
                return None

            # Standardize column names to match our format
            df = df.rename(
                columns={
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Volume": "volume",
                }
            )

            # Ensure timezone-aware index
            if df.index.tz is None:
                df.index = df.index.tz_localize("UTC")
            else:
                df.index = df.index.tz_convert("UTC")

            # Reset index to have timestamp column
            df = df.reset_index()
            df = df.rename(columns={"Date": "timestamp"})

            return df

        except Exception as e:
            logger.warning(
                "Failed to fetch external data",
                extra={"symbol": symbol, "error": str(e)},
            )
            return None

    def _check_freshness(self, our_data: pd.DataFrame) -> list[str]:
        """Check if our data is recent enough.

        Args:
            our_data: Our data to check

        Returns:
            List of freshness issues

        """
        issues = []

        if our_data.empty:
            return issues

        # Get the most recent timestamp
        if "timestamp" in our_data.columns:
            latest_timestamp = pd.to_datetime(our_data["timestamp"]).max()
        else:
            # Timestamp is the index
            latest_timestamp = our_data.index.max()

        # Convert to datetime if needed
        if isinstance(latest_timestamp, str):
            latest_timestamp = pd.to_datetime(latest_timestamp)

        # Ensure timezone-aware
        if latest_timestamp.tzinfo is None:
            latest_timestamp = latest_timestamp.tz_localize("UTC")

        # Check if data is stale (more than 2 days old, accounting for weekends)
        now = datetime.now(UTC)
        age_hours = (now - latest_timestamp).total_seconds() / 3600

        # Allow up to 72 hours (3 days) to account for weekends
        if age_hours > 72:
            issues.append(
                f"Data is stale: latest timestamp is {latest_timestamp.isoformat()}, "
                f"age is {age_hours:.1f} hours"
            )

        return issues

    def _check_completeness(
        self,
        our_data: pd.DataFrame,
        external_data: pd.DataFrame,
    ) -> list[str]:
        """Check if we have data for all dates that external source has.

        Args:
            our_data: Our data
            external_data: External data

        Returns:
            List of completeness issues

        """
        issues = []

        # Extract dates from both datasets
        our_dates = set(pd.to_datetime(our_data["timestamp"]).dt.date)
        external_dates = set(pd.to_datetime(external_data["timestamp"]).dt.date)

        # Find missing dates (in external but not in ours)
        missing_dates = external_dates - our_dates

        if missing_dates:
            # Only flag as issue if we're missing recent dates (last 2 days)
            recent_missing = [
                d
                for d in missing_dates
                if (datetime.now(UTC).date() - d).days <= 2
            ]

            if recent_missing:
                issues.append(
                    f"Missing {len(recent_missing)} recent trading day(s): "
                    f"{sorted(recent_missing)}"
                )

        return issues

    def _check_price_accuracy(
        self,
        our_data: pd.DataFrame,
        external_data: pd.DataFrame,
        tolerance_pct: float = 2.0,
    ) -> list[str]:
        """Check if our prices match external source within tolerance.

        Args:
            our_data: Our data
            external_data: External data
            tolerance_pct: Acceptable percentage difference

        Returns:
            List of accuracy issues

        """
        issues = []

        # Merge on date (not exact timestamp, as times may differ)
        our_data = our_data.copy()
        external_data = external_data.copy()

        our_data["date"] = pd.to_datetime(our_data["timestamp"]).dt.date
        external_data["date"] = pd.to_datetime(external_data["timestamp"]).dt.date

        merged = our_data.merge(
            external_data,
            on="date",
            suffixes=("_ours", "_external"),
        )

        if merged.empty:
            issues.append("No overlapping dates found for comparison")
            return issues

        # Check close prices (most important for strategies)
        for _, row in merged.iterrows():
            our_close = row["close_ours"]
            ext_close = row["close_external"]
            date = row["date"]

            # Calculate percentage difference
            if ext_close == 0:
                continue

            pct_diff = abs(our_close - ext_close) / ext_close * 100

            if pct_diff > tolerance_pct:
                issues.append(
                    f"Price mismatch on {date}: "
                    f"ours={our_close:.2f}, external={ext_close:.2f}, "
                    f"diff={pct_diff:.1f}%"
                )

        return issues
