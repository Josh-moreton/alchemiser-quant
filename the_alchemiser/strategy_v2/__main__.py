"""Bootstrap entrypoint for running strategy_v2 standalone."""

from __future__ import annotations

from dependency_injector import providers

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.logging import configure_application_logging, get_logger

from . import register_strategy_handlers
from .adapters.transports import StrategyTransports, build_strategy_transports

logger = get_logger(__name__)


def main(env: str = "development", transports: StrategyTransports | None = None) -> ApplicationContainer:
    """Configure logging, wire DI, and register handlers for standalone runs."""

    configure_application_logging()
    container = ApplicationContainer.create_for_environment(env)

    transport_bundle = transports or build_strategy_transports(container)
    container.services.event_bus.override(providers.Object(transport_bundle.event_bus))
    container.strategy_transports = transport_bundle

    register_strategy_handlers(container, event_bus=transport_bundle.event_bus)
    logger.info(
        "Strategy module bootstrapped",
        extra={"environment": env, "component": "strategy_v2.__main__"},
    )
    return container


if __name__ == "__main__":  # pragma: no cover - manual execution only
    main()

