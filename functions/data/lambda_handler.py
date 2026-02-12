"""Business Unit: data | Status: current.

Lambda handler for data microservice.

This is the entry point for the Data Lambda which fetches new market data from
Alpaca and stores it in S3 Parquet format.

Triggered by:
- EventBridge Schedule (daily at 4:00 AM UTC, Tue-Sat to catch Mon-Fri data)
- MarketDataFetchRequested events (on-demand from strategy lambdas)
- Manual invocation for testing or initial seeding
"""

from __future__ import annotations

from typing import Any

from handlers import FetchRequestHandler, ScheduledRefreshHandler

from the_alchemiser.shared.logging import configure_application_logging, get_logger

configure_application_logging()

logger = get_logger(__name__)

_fetch_handler = FetchRequestHandler()
_refresh_handler = ScheduledRefreshHandler()


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Route data Lambda invocations to the appropriate handler.

    Args:
        event: Lambda event (varies by trigger type)
        context: Lambda context

    Returns:
        Response with refresh statistics

    """
    if _is_fetch_request_event(event):
        return _fetch_handler.handle(event)

    return _refresh_handler.handle(event)


def _is_fetch_request_event(event: dict[str, Any]) -> bool:
    """Check if event is a MarketDataFetchRequested EventBridge event."""
    detail_type = event.get("detail-type")
    source = event.get("source", "")
    return detail_type == "MarketDataFetchRequested" and source.startswith("alchemiser.")
