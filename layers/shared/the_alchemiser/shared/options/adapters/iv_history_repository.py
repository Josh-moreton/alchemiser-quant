"""Business Unit: shared | Status: current.

DynamoDB repository for historical implied volatility data.

Stores daily ATM IV snapshots for hedge underlyings (QQQ, SPY) to enable
actual 252-day rolling IV percentile calculations instead of approximations.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

__all__ = ["IVHistoryRecord", "IVHistoryRepository"]

# DynamoDB exception types for error handling
DynamoDBException = (ClientError, BotoCoreError)

# Minimum observations required for reliable percentile calculation
# 126 = ~6 months of trading days (minimum)
# 252 = ~1 year of trading days (preferred)
MIN_OBSERVATIONS_FOR_PERCENTILE = 126
PREFERRED_OBSERVATIONS = 252


class IVHistoryRecord:
    """Record of a single daily IV observation."""

    __slots__ = (
        "atm_iv",
        "dte_used",
        "put_25delta_iv",
        "record_date",
        "timestamp",
        "underlying_symbol",
    )

    def __init__(
        self,
        underlying_symbol: str,
        record_date: date,
        atm_iv: Decimal,
        put_25delta_iv: Decimal,
        dte_used: int,
        timestamp: datetime,
    ) -> None:
        """Initialize IV history record.

        Args:
            underlying_symbol: Underlying ETF symbol (QQQ, SPY)
            record_date: Date of the IV observation
            atm_iv: ATM implied volatility (annualized, e.g., 0.20 = 20%)
            put_25delta_iv: 25-delta put IV (annualized)
            dte_used: Days to expiration of options used for IV calculation
            timestamp: Precise timestamp when IV was captured

        """
        self.underlying_symbol = underlying_symbol.upper()
        self.record_date = record_date
        self.atm_iv = atm_iv
        self.put_25delta_iv = put_25delta_iv
        self.dte_used = dte_used
        self.timestamp = timestamp


class IVHistoryRepository:
    """Repository for historical IV data using DynamoDB.

    Table structure:
    - PK (partition key): underlying_symbol (e.g., "QQQ")
    - SK (sort key): record_date (ISO format, e.g., "2026-01-30")

    This design allows efficient querying of:
    - All IV history for an underlying (query by PK)
    - Rolling window of IV data (query by PK with SK range)
    """

    def __init__(self, table_name: str) -> None:
        """Initialize repository.

        Args:
            table_name: DynamoDB table name

        """
        self._dynamodb = boto3.resource("dynamodb")
        self._table = self._dynamodb.Table(table_name)
        logger.debug("Initialized IV history repository", table=table_name)

    def record_daily_iv(
        self,
        underlying_symbol: str,
        atm_iv: Decimal,
        put_25delta_iv: Decimal,
        dte_used: int,
        record_date: date | None = None,
    ) -> bool:
        """Record a daily IV observation.

        Idempotent by date - only one record per underlying per day.
        If a record already exists for the date, it will be overwritten.

        Args:
            underlying_symbol: Underlying ETF symbol (QQQ, SPY)
            atm_iv: ATM implied volatility (annualized)
            put_25delta_iv: 25-delta put IV (annualized)
            dte_used: Days to expiration of options used
            record_date: Date of observation (defaults to today)

        Returns:
            True if successful, False on error

        """
        if record_date is None:
            record_date = datetime.now(UTC).date()

        now = datetime.now(UTC)
        # Set TTL to 400 days to maintain >252 days of rolling data
        ttl = int((now + timedelta(days=400)).timestamp())

        symbol = underlying_symbol.upper()

        item: dict[str, Any] = {
            "underlying_symbol": symbol,
            "record_date": record_date.isoformat(),
            "atm_iv": str(atm_iv),
            "put_25delta_iv": str(put_25delta_iv),
            "dte_used": dte_used,
            "timestamp": now.isoformat(),
            "ttl": ttl,
        }

        try:
            self._table.put_item(Item=item)
            logger.info(
                "Recorded daily IV snapshot",
                underlying_symbol=symbol,
                record_date=record_date.isoformat(),
                atm_iv=str(atm_iv),
                put_25delta_iv=str(put_25delta_iv),
            )
            return True
        except DynamoDBException as e:
            logger.error(
                "Failed to record daily IV",
                underlying_symbol=symbol,
                record_date=record_date.isoformat(),
                error=str(e),
                exc_info=True,
            )
            return False

    def get_rolling_iv_data(
        self,
        underlying_symbol: str,
        days: int = PREFERRED_OBSERVATIONS,
        as_of: date | None = None,
    ) -> list[IVHistoryRecord]:
        """Fetch rolling window of IV data.

        Args:
            underlying_symbol: Underlying ETF symbol
            days: Number of days to fetch (default: 252 = 1 year)
            as_of: End date of the window (defaults to today)

        Returns:
            List of IVHistoryRecord sorted by date ascending

        """
        if as_of is None:
            as_of = datetime.now(UTC).date()

        # Calculate start date (N calendar days back, but we'll get fewer records
        # since markets aren't open every day)
        # Use 1.5x multiplier to account for weekends/holidays
        calendar_days_back = int(days * 1.5)
        start_date = as_of - timedelta(days=calendar_days_back)

        symbol = underlying_symbol.upper()

        try:
            response = self._table.query(
                KeyConditionExpression=(
                    "underlying_symbol = :symbol AND record_date BETWEEN :start AND :end"
                ),
                ExpressionAttributeValues={
                    ":symbol": symbol,
                    ":start": start_date.isoformat(),
                    ":end": as_of.isoformat(),
                },
                ScanIndexForward=True,  # Ascending order by date
            )

            items = response.get("Items", [])

            # Handle pagination if needed
            while "LastEvaluatedKey" in response:
                response = self._table.query(
                    KeyConditionExpression=(
                        "underlying_symbol = :symbol AND record_date BETWEEN :start AND :end"
                    ),
                    ExpressionAttributeValues={
                        ":symbol": symbol,
                        ":start": start_date.isoformat(),
                        ":end": as_of.isoformat(),
                    },
                    ScanIndexForward=True,
                    ExclusiveStartKey=response["LastEvaluatedKey"],
                )
                items.extend(response.get("Items", []))

            records = [self._item_to_record(item) for item in items]

            logger.info(
                "Fetched rolling IV data",
                underlying_symbol=symbol,
                start_date=start_date.isoformat(),
                end_date=as_of.isoformat(),
                record_count=len(records),
            )

            return records

        except DynamoDBException as e:
            logger.error(
                "Failed to fetch rolling IV data",
                underlying_symbol=symbol,
                error=str(e),
                exc_info=True,
            )
            return []

    def calculate_percentile(
        self,
        underlying_symbol: str,
        current_iv: Decimal,
        days: int = PREFERRED_OBSERVATIONS,
    ) -> tuple[Decimal, int]:
        """Calculate IV percentile from historical data.

        Args:
            underlying_symbol: Underlying ETF symbol
            current_iv: Current ATM IV to rank
            days: Number of days of history to use (default: 252)

        Returns:
            Tuple of (percentile 0-100, observation_count)

        """
        records = self.get_rolling_iv_data(underlying_symbol, days)

        if not records:
            logger.warning(
                "No historical IV data available for percentile calculation",
                underlying_symbol=underlying_symbol,
            )
            return Decimal("-1"), 0  # Signal no data

        # Extract ATM IV values
        historical_ivs = [r.atm_iv for r in records]
        observation_count = len(historical_ivs)

        # Calculate percentile: % of historical values below current
        count_below = sum(1 for iv in historical_ivs if iv < current_iv)
        percentile = Decimal(str(count_below)) / Decimal(str(observation_count)) * Decimal("100")

        logger.info(
            "Calculated IV percentile from historical data",
            underlying_symbol=underlying_symbol,
            current_iv=str(current_iv),
            percentile=str(percentile),
            observation_count=observation_count,
            min_iv=str(min(historical_ivs)),
            max_iv=str(max(historical_ivs)),
        )

        return percentile, observation_count

    def _item_to_record(self, item: dict[str, Any]) -> IVHistoryRecord:
        """Convert DynamoDB item to IVHistoryRecord.

        Args:
            item: DynamoDB item dict

        Returns:
            IVHistoryRecord

        """
        return IVHistoryRecord(
            underlying_symbol=item["underlying_symbol"],
            record_date=date.fromisoformat(item["record_date"]),
            atm_iv=Decimal(str(item["atm_iv"])),
            put_25delta_iv=Decimal(str(item["put_25delta_iv"])),
            dte_used=int(item["dte_used"]),
            timestamp=datetime.fromisoformat(item["timestamp"]),
        )

    def get_latest_record(
        self,
        underlying_symbol: str,
    ) -> IVHistoryRecord | None:
        """Get the most recent IV record for an underlying.

        Args:
            underlying_symbol: Underlying ETF symbol

        Returns:
            Most recent IVHistoryRecord or None if not found

        """
        symbol = underlying_symbol.upper()

        try:
            response = self._table.query(
                KeyConditionExpression="underlying_symbol = :symbol",
                ExpressionAttributeValues={":symbol": symbol},
                ScanIndexForward=False,  # Descending order (newest first)
                Limit=1,
            )

            items = response.get("Items", [])
            if not items:
                return None

            return self._item_to_record(items[0])

        except DynamoDBException as e:
            logger.error(
                "Failed to get latest IV record",
                underlying_symbol=symbol,
                error=str(e),
                exc_info=True,
            )
            return None

    def has_sufficient_history(
        self,
        underlying_symbol: str,
        min_observations: int = MIN_OBSERVATIONS_FOR_PERCENTILE,
    ) -> bool:
        """Check if sufficient historical data exists for percentile calculation.

        Args:
            underlying_symbol: Underlying ETF symbol
            min_observations: Minimum number of observations required

        Returns:
            True if sufficient history exists

        """
        records = self.get_rolling_iv_data(underlying_symbol, days=min_observations)
        has_sufficient = len(records) >= min_observations

        logger.info(
            "Checked IV history sufficiency",
            underlying_symbol=underlying_symbol,
            observation_count=len(records),
            min_required=min_observations,
            has_sufficient=has_sufficient,
        )

        return has_sufficient
