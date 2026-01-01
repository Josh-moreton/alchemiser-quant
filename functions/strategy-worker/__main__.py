"""Business Unit: Strategy | Status: current.

Bootstrap entrypoint for running strategy_v2 standalone.

Note: Strategy module is now invoked exclusively via Lambda handler from
the Strategy Orchestrator. This module provides local testing support.
"""

from __future__ import annotations

from adapters.transports import StrategyTransports, build_strategy_transports
from dependency_injector import providers

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.logging import configure_application_logging, get_logger

logger = get_logger(__name__)


def main(
    env: str = "development", transports: StrategyTransports | None = None
) -> ApplicationContainer:
    """Configure logging, wire DI for standalone runs."""
    configure_application_logging()
    container = ApplicationContainer.create_for_environment(env)

    transport_bundle = transports or build_strategy_transports(container)
    container.services.event_bus.override(providers.Object(transport_bundle.event_bus))

    # Store transport bundle on container for test inspection and debugging.
    # This is intentional dynamic attribute assignment - while it bypasses
    # the DI framework's normal provider mechanism, it's appropriate here because:
    # 1. Transports are already injected via event_bus override
    # 2. This attribute is only for observability (tests, debugging)
    # 3. The container is ephemeral (created per invocation)
    container.strategy_transports = transport_bundle

    logger.info(
        "Strategy module bootstrapped",
        extra={"environment": env, "component": "strategy_v2.__main__"},
    )
    return container


if __name__ == "__main__":  # pragma: no cover - manual execution only
    main()
