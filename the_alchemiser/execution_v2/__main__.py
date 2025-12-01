"""Bootstrap entrypoint for running execution_v2 standalone."""

from __future__ import annotations

from dependency_injector import providers

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.logging import configure_application_logging, get_logger

from . import register_execution_handlers
from .adapters.transports import ExecutionTransports, build_execution_transports

logger = get_logger(__name__)


def main(env: str = "development", transports: ExecutionTransports | None = None) -> ApplicationContainer:
    """Configure logging, wire DI, and register handlers for standalone runs."""

    configure_application_logging()
    container = ApplicationContainer.create_for_environment(env)

    transport_bundle = transports or build_execution_transports(container)
    container.services.event_bus.override(providers.Object(transport_bundle.event_bus))
    container.execution_transports = transport_bundle

    register_execution_handlers(container, event_bus=transport_bundle.event_bus)
    logger.info(
        "Execution module bootstrapped",
        extra={"environment": env, "component": "execution_v2.__main__"},
    )
    return container


if __name__ == "__main__":  # pragma: no cover - manual execution only
    main()

