"""Business Unit: Reporting | Status: current.

Bootstrap entrypoint for running reporting module standalone.

Architecture Note:
    Unlike other modules, the reporting module avoids importing ApplicationContainer
    to keep dependencies minimal. This module creates a lightweight EventBus directly
    rather than pulling in heavy dependencies (pandas, numpy) via the container.
"""

from __future__ import annotations

from dataclasses import dataclass

from the_alchemiser.shared.logging import configure_application_logging, get_logger

from .adapters.transports import ReportingTransports, build_reporting_transports_lightweight

logger = get_logger(__name__)


@dataclass
class LightweightReportingContext:
    """Lightweight context for the reporting module (no ApplicationContainer).

    This replaces ApplicationContainer for the reporting module to avoid
    pulling in heavy dependencies.
    """

    transports: ReportingTransports
    environment: str


def main(
    env: str = "development", transports: ReportingTransports | None = None
) -> LightweightReportingContext:
    """Configure logging and wire transports for standalone reporting runs.

    Unlike other modules, this does NOT use ApplicationContainer to avoid
    pulling in heavy dependencies (pandas, numpy) that are not needed for
    PDF report generation.

    Args:
        env: Environment name (development, testing, production).
        transports: Optional pre-configured transports bundle.

    Returns:
        LightweightReportingContext with configured transports.

    """
    configure_application_logging()

    transport_bundle = transports or build_reporting_transports_lightweight()

    context = LightweightReportingContext(
        transports=transport_bundle,
        environment=env,
    )

    logger.info(
        "Reporting module bootstrapped (lightweight mode)",
        extra={"environment": env, "component": "reporting.__main__"},
    )

    return context


if __name__ == "__main__":  # pragma: no cover - manual execution only
    main()
