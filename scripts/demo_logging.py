"""Emit sample structured log events."""
from __future__ import annotations

from the_alchemiser.logging import configure_logging, get_logger, context


def main() -> None:
    configure_logging(env="DEV", service="alchemiser", version="demo", region="local")
    logger = get_logger(__name__)

    with context(request_id="req-1"):
        logger.info("Starting demo", extra={"event": "demo.start"})

    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("Division failed", extra={"event": "demo.error"})

    with context(symbol="AAPL", order_id="123"):
        logger.info(
            "Placed order",
            extra={"event": "order.placed", "symbol": "AAPL", "order_id": "123"},
        )


if __name__ == "__main__":
    main()
