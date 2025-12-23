"""Business Unit: data | Status: current.

Data quality validation by comparing S3 cached data against external source (yfinance).

Validates price and date accuracy of market data stored in S3 by comparing
against Yahoo Finance data. Generates detailed quality reports highlighting
discrepancies for manual review and data integrity monitoring.
"""

from __future__ import annotations

import csv
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from the_alchemiser.shared.logging import get_logger

from .market_data_store import MarketDataStore

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

logger = get_logger(__name__)


@dataclass(frozen=True)
class ValidationDiscrepancy:
    """Represents a data quality discrepancy found during validation.

    Attributes:
        symbol: Ticker symbol
        date: Date of discrepancy (YYYY-MM-DD)
        field: Field with discrepancy (close, open, high, low, volume)
        alpaca_value: Value from Alpaca/S3 cache
        yfinance_value: Value from Yahoo Finance
        diff_pct: Percentage difference

    """

    symbol: str
    date: str
    field: str
    alpaca_value: Decimal
    yfinance_value: Decimal
    diff_pct: Decimal


@dataclass(frozen=True)
class ValidationResult:
    """Results from data quality validation run.

    Attributes:
        symbols_checked: Total symbols validated
        symbols_passed: Symbols with no discrepancies
        symbols_failed: Symbols with discrepancies
        discrepancies: List of all discrepancies found
        validation_date: Date validation was run

    """

    symbols_checked: int
    symbols_passed: int
    symbols_failed: int
    discrepancies: list[ValidationDiscrepancy]
    validation_date: str


class DataQualityValidator:
    """Validates market data quality by comparing S3 cache against yfinance.

    Compares OHLCV data from S3 (sourced from Alpaca) against Yahoo Finance
    to detect discrepancies. Generates CSV reports for manual review.

    Attributes:
        market_data_store: S3-backed market data store
        price_tolerance_pct: Tolerance for price differences (default 0.5%)
        volume_tolerance_pct: Tolerance for volume differences (default 5%)

    """

    def __init__(
        self,
        market_data_store: MarketDataStore,
        price_tolerance_pct: Decimal = Decimal("0.5"),
        volume_tolerance_pct: Decimal = Decimal("5.0"),
    ) -> None:
        """Initialize data quality validator.

        Args:
            market_data_store: Store for accessing cached market data
            price_tolerance_pct: Acceptable price difference percentage
            volume_tolerance_pct: Acceptable volume difference percentage

        """
        self.store = market_data_store
        self.price_tolerance_pct = price_tolerance_pct
        self.volume_tolerance_pct = volume_tolerance_pct

    def validate_symbol(
        self, symbol: str, lookback_days: int = 5
    ) -> tuple[bool, list[ValidationDiscrepancy]]:
        """Validate a single symbol's data against yfinance.

        Args:
            symbol: Ticker symbol to validate
            lookback_days: Number of recent days to validate

        Returns:
            Tuple of (passed, discrepancies_list)

        """
        discrepancies: list[ValidationDiscrepancy] = []

        try:
            # Get data from S3
            alpaca_df = self.store.read_symbol_data(symbol)
            if alpaca_df is None or alpaca_df.empty:
                logger.warning("No data in S3 for symbol", symbol=symbol)
                return False, discrepancies

            # Ensure timestamp column exists
            if "timestamp" not in alpaca_df.columns:
                logger.error("Missing timestamp column in S3 data", symbol=symbol)
                return False, discrepancies

            # Filter to recent days
            alpaca_df["timestamp"] = pd.to_datetime(alpaca_df["timestamp"])
            cutoff_date = datetime.now(UTC) - timedelta(days=lookback_days)
            alpaca_df = alpaca_df[alpaca_df["timestamp"] >= cutoff_date].copy()

            if alpaca_df.empty:
                logger.warning(
                    "No recent data in S3", symbol=symbol, lookback_days=lookback_days
                )
                return False, discrepancies

            # Fetch from yfinance (lazy import to avoid cold start penalty)
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            yf_df = ticker.history(period=f"{lookback_days}d", interval="1d")

            if yf_df.empty:
                logger.warning("No data from yfinance", symbol=symbol)
                return False, discrepancies

            # Normalize yfinance data (column names are capitalized)
            yf_df.index = pd.to_datetime(yf_df.index)
            yf_df.columns = yf_df.columns.str.lower()

            # Compare date by date
            for _, alpaca_row in alpaca_df.iterrows():
                date = alpaca_row["timestamp"].date()
                date_str = date.strftime("%Y-%m-%d")

                # Find matching date in yfinance data
                yf_matches = yf_df[yf_df.index.date == date]
                if yf_matches.empty:
                    continue

                yf_row = yf_matches.iloc[0]

                # Compare each field
                for field in ["close", "open", "high", "low"]:
                    alpaca_val = Decimal(str(alpaca_row[field]))
                    yf_val = Decimal(str(yf_row[field]))

                    # Calculate percentage difference
                    if yf_val != Decimal("0"):
                        diff_pct = abs((alpaca_val - yf_val) / yf_val * Decimal("100"))

                        if diff_pct > self.price_tolerance_pct:
                            discrepancies.append(
                                ValidationDiscrepancy(
                                    symbol=symbol,
                                    date=date_str,
                                    field=field,
                                    alpaca_value=alpaca_val,
                                    yfinance_value=yf_val,
                                    diff_pct=diff_pct,
                                )
                            )

                # Compare volume (higher tolerance)
                if "volume" in alpaca_row and "volume" in yf_row:
                    alpaca_vol = Decimal(str(alpaca_row["volume"]))
                    yf_vol = Decimal(str(yf_row["volume"]))

                    if yf_vol != Decimal("0"):
                        vol_diff_pct = abs((alpaca_vol - yf_vol) / yf_vol * Decimal("100"))

                        if vol_diff_pct > self.volume_tolerance_pct:
                            discrepancies.append(
                                ValidationDiscrepancy(
                                    symbol=symbol,
                                    date=date_str,
                                    field="volume",
                                    alpaca_value=alpaca_vol,
                                    yfinance_value=yf_vol,
                                    diff_pct=vol_diff_pct,
                                )
                            )

            passed = len(discrepancies) == 0
            if passed:
                logger.info("Validation passed", symbol=symbol)
            else:
                logger.warning(
                    "Validation failed",
                    symbol=symbol,
                    discrepancies_count=len(discrepancies),
                )

            return passed, discrepancies

        except Exception as e:
            logger.error(
                "Validation error",
                symbol=symbol,
                error=str(e),
                exc_info=True,
            )
            return False, discrepancies

    def validate_all_symbols(
        self, symbols: list[str] | None = None, lookback_days: int = 5
    ) -> ValidationResult:
        """Validate all symbols in S3 or a specific list.

        Args:
            symbols: List of symbols to validate (None = all symbols in S3)
            lookback_days: Number of recent days to validate per symbol

        Returns:
            ValidationResult with summary and all discrepancies

        """
        symbols_to_check = symbols or self.store.list_symbols()
        validation_date = datetime.now(UTC).strftime("%Y-%m-%d")

        logger.info(
            "Starting data quality validation",
            symbols_count=len(symbols_to_check),
            lookback_days=lookback_days,
        )

        symbols_passed = 0
        symbols_failed = 0
        all_discrepancies: list[ValidationDiscrepancy] = []

        for symbol in symbols_to_check:
            passed, discrepancies = self.validate_symbol(symbol, lookback_days)

            if passed:
                symbols_passed += 1
            else:
                symbols_failed += 1

            all_discrepancies.extend(discrepancies)

        result = ValidationResult(
            symbols_checked=len(symbols_to_check),
            symbols_passed=symbols_passed,
            symbols_failed=symbols_failed,
            discrepancies=all_discrepancies,
            validation_date=validation_date,
        )

        logger.info(
            "Data quality validation completed",
            symbols_checked=result.symbols_checked,
            symbols_passed=result.symbols_passed,
            symbols_failed=result.symbols_failed,
            discrepancies_found=len(result.discrepancies),
        )

        return result

    def generate_report_csv(self, validation_result: ValidationResult) -> Path:
        """Generate CSV report from validation results.

        Args:
            validation_result: Results from validation run

        Returns:
            Path to generated CSV file

        """
        # Create temp file for CSV
        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".csv",
            delete=False,
            prefix=f"data_quality_report_{validation_result.validation_date}_",
        )

        with temp_file as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(
                [
                    "Symbol",
                    "Date",
                    "Field",
                    "Alpaca Value",
                    "YFinance Value",
                    "Diff %",
                ]
            )

            # Write discrepancies
            for disc in validation_result.discrepancies:
                writer.writerow(
                    [
                        disc.symbol,
                        disc.date,
                        disc.field,
                        str(disc.alpaca_value),
                        str(disc.yfinance_value),
                        f"{disc.diff_pct:.2f}",
                    ]
                )

        report_path = Path(temp_file.name)
        logger.info(
            "Generated validation report CSV",
            report_path=str(report_path),
            discrepancies_count=len(validation_result.discrepancies),
        )

        return report_path

    def upload_report_to_s3(
        self,
        report_path: Path,
        validation_date: str,
        s3_client: S3Client | None = None,
    ) -> str:
        """Upload validation report to S3.

        Args:
            report_path: Path to report CSV file
            validation_date: Date of validation (YYYY-MM-DD)
            s3_client: Optional S3 client (uses store's client if None)

        Returns:
            S3 key of uploaded report

        """
        s3 = s3_client or self.store.s3_client

        # Generate S3 key
        s3_key = f"data-quality-reports/{validation_date}_validation_report.csv"

        # Upload to S3
        with report_path.open("rb") as f:
            s3.put_object(
                Bucket=self.store.bucket_name,
                Key=s3_key,
                Body=f.read(),
                ContentType="text/csv",
            )

        logger.info(
            "Uploaded validation report to S3",
            s3_bucket=self.store.bucket_name,
            s3_key=s3_key,
        )

        return s3_key
