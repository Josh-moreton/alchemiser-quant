"""Business Unit: Portfolio | Status: current.

Bootstrap entrypoint for running portfolio_v2 standalone.
"""

from __future__ import annotations

from dependency_injector import providers

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.logging import configure_application_logging, get_logger

from . import register_portfolio_handlers
from .adapters.transports import PortfolioTransports, build_portfolio_transports
from .wiring import register_portfolio

logger = get_logger(__name__)


def main(
    env: str = "development", transports: PortfolioTransports | None = None
) -> ApplicationContainer:
    """Configure logging, wire DI, and register handlers for standalone runs."""
    configure_application_logging()
    container = ApplicationContainer()
    register_portfolio(container)

    transport_bundle = transports or build_portfolio_transports(container)
    container.services.event_bus.override(providers.Object(transport_bundle.event_bus))

    # Store transport bundle on container for test inspection and debugging.
    # This is intentional dynamic attribute assignment - while it bypasses
    # the DI framework's normal provider mechanism, it's appropriate here because:
    # 1. Transports are already injected via event_bus override
    # 2. This attribute is only for observability (tests, debugging)
    # 3. The container is ephemeral (created per invocation)
    container.portfolio_transports = transport_bundle

    register_portfolio_handlers(container, event_bus=transport_bundle.event_bus)
    logger.info(
        "Portfolio module bootstrapped",
        extra={"environment": env, "component": "portfolio_v2.__main__"},
    )
    return container


if __name__ == "__main__":  # pragma: no cover - manual execution only
    main()
