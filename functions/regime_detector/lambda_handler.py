"""Business Unit: regime_detector | Status: current.

Lambda handler for Market Regime Detector microservice.

This Lambda runs daily after US market close (4:30 PM ET) to:
1. Download latest SPY data from Alpaca
2. Run HMM-based regime classification
3. Cache the current regime in DynamoDB

The cached regime is read by Strategy Orchestrator before each
trading session to adjust strategy allocations.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pandas as pd

from the_alchemiser.shared.events import WorkflowFailed
from the_alchemiser.shared.events.eventbridge_publisher import publish_to_eventbridge
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.regime.classifier import HMMRegimeClassifier
from the_alchemiser.shared.regime.repository import RegimeStateRepository

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)


def get_spy_data_from_alpaca(days: int = 365) -> pd.DataFrame:
    """Fetch SPY OHLC data from Alpaca.

    Args:
        days: Number of historical days to fetch

    Returns:
        DataFrame with Date index and OHLC columns

    Raises:
        RuntimeError: If Alpaca credentials are missing or API fails

    """
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    api_key = os.environ.get("ALPACA__KEY")
    api_secret = os.environ.get("ALPACA__SECRET")

    if not api_key or not api_secret:
        raise RuntimeError("ALPACA__KEY and ALPACA__SECRET environment variables required")

    client = StockHistoricalDataClient(api_key, api_secret)

    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=days)

    request = StockBarsRequest(
        symbol_or_symbols="SPY",
        start=start_date,
        end=end_date,
        timeframe=TimeFrame.Day,
    )

    bars = client.get_stock_bars(request)

    # Convert to DataFrame
    data = []
    for bar in bars["SPY"]:
        data.append(
            {
                "Date": bar.timestamp,
                "Open": float(bar.open),
                "High": float(bar.high),
                "Low": float(bar.low),
                "Close": float(bar.close),
                "Volume": int(bar.volume),
            }
        )

    df = pd.DataFrame(data)
    df.set_index("Date", inplace=True)
    df.sort_index(inplace=True)

    logger.info(
        "Fetched SPY data from Alpaca",
        extra={
            "days_requested": days,
            "rows_returned": len(df),
            "start_date": str(df.index.min()),
            "end_date": str(df.index.max()),
        },
    )

    return df


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle scheduled invocation to detect market regime.

    This handler:
    1. Fetches SPY data from Alpaca
    2. Runs HMM regime classification
    3. Stores result in DynamoDB

    Args:
        event: Lambda event (from EventBridge schedule)
        context: Lambda context

    Returns:
        Response with regime classification result

    """
    correlation_id = event.get("correlation_id") or f"regime-{uuid.uuid4()}"

    logger.info(
        "Regime Detector Lambda invoked",
        extra={
            "correlation_id": correlation_id,
            "event_source": event.get("source", "schedule"),
        },
    )

    try:
        # Load settings
        table_name = os.environ.get("REGIME_STATE_TABLE_NAME", "")
        if not table_name:
            raise ValueError("REGIME_STATE_TABLE_NAME environment variable required")

        lookback_days = int(os.environ.get("REGIME_LOOKBACK_DAYS", "365"))
        min_regime_duration = int(os.environ.get("REGIME_MIN_DURATION_DAYS", "10"))
        use_recovery = os.environ.get("REGIME_USE_RECOVERY", "true").lower() == "true"

        # Fetch SPY data
        spy_data = get_spy_data_from_alpaca(days=lookback_days)

        # Initialize classifier
        classifier = HMMRegimeClassifier(
            min_regime_duration=min_regime_duration,
            use_recovery=use_recovery,
        )

        # Prepare features
        features_df = classifier.prepare_features(spy_data)

        # Fit model and classify
        classifier.fit(features_df)
        regime_state = classifier.classify_with_smoothing(features_df)

        # Store in DynamoDB
        repository = RegimeStateRepository(table_name=table_name)
        repository.put_regime_state(regime_state)

        logger.info(
            "Regime detection completed",
            extra={
                "correlation_id": correlation_id,
                "regime": regime_state.regime.value,
                "probability": str(regime_state.probability),
                "bull_probability": str(regime_state.bull_probability),
                "spy_close": str(regime_state.spy_close),
                "lookback_days": regime_state.lookback_days,
            },
        )

        return {
            "statusCode": 200,
            "body": {
                "status": "success",
                "correlation_id": correlation_id,
                "regime": regime_state.regime.value,
                "probability": str(regime_state.probability),
                "bull_probability": str(regime_state.bull_probability),
                "spy_close": str(regime_state.spy_close),
                "timestamp": regime_state.timestamp.isoformat(),
            },
        }

    except Exception as e:
        logger.error(
            "Regime Detector Lambda failed",
            extra={
                "correlation_id": correlation_id,
                "error": str(e),
            },
            exc_info=True,
        )

        # Publish WorkflowFailed to EventBridge
        try:
            failure_event = WorkflowFailed(
                correlation_id=correlation_id,
                causation_id=correlation_id,
                event_id=f"workflow-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="regime_detector",
                source_component="lambda_handler",
                workflow_type="regime_detection",
                failure_reason=str(e),
                failure_step="regime_classification",
                error_details={"exception_type": type(e).__name__},
            )
            publish_to_eventbridge(failure_event)
        except Exception as pub_error:
            logger.error(
                "Failed to publish WorkflowFailed event",
                extra={"error": str(pub_error)},
            )

        return {
            "statusCode": 500,
            "body": {
                "status": "error",
                "correlation_id": correlation_id,
                "error": str(e),
            },
        }
