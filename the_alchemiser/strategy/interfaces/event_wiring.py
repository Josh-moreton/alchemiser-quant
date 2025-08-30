"""Business Unit: strategy & signal generation | Status: current

Event wiring for Strategy context event subscriptions.

This module registers event handlers with the EventBus to enable the Strategy context
to receive and process events from other bounded contexts.

Note: Currently Strategy context is primarily a producer of events (signals),
but this module is provided for future extensibility if Strategy context needs
to consume events from other contexts.
"""

from __future__ import annotations

import logging

from the_alchemiser.cross_context.eventing.event_bus import EventBus

logger = logging.getLogger(__name__)


def wire_strategy_event_subscriptions(
    event_bus: EventBus,
) -> None:
    """Wire Strategy context event subscriptions.
    
    Currently Strategy context is primarily an event producer (signals),
    but this function is provided for future extensibility.
    
    Args:
        event_bus: EventBus instance for subscription

    """
    logger.info("Wiring Strategy context event subscriptions...")
    
    # TODO: Add strategy event subscriptions as needed
    # For example, Strategy context might want to:
    # - Receive portfolio performance feedback
    # - Listen to market regime changes
    # - Subscribe to risk management alerts
    
    logger.info("Strategy context event subscriptions wired successfully")