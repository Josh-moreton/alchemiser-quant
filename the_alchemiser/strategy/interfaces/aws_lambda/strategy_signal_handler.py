"""Business Unit: strategy & signal generation | Status: current.

AWS Lambda handler for scheduled strategy signal generation.

This handler is triggered by CloudWatch Events/EventBridge on a schedule
(e.g., daily market open) and invokes the GenerateSignalsUseCase to produce
strategy signals for cross-context publication.

Trigger: CloudWatch Event / EventBridge (scheduled)
Action: GenerateSignalsUseCase -> publish SignalContractV1 events
"""

from __future__ import annotations

import logging
from typing import Any

from the_alchemiser.shared_kernel.exceptions.base_exceptions import (
    ConfigurationError,
    DataAccessError,
)
from the_alchemiser.shared_kernel.value_objects.symbol import Symbol
from the_alchemiser.strategy.domain.exceptions import PublishError, SymbolNotFoundError

from .bootstrap import bootstrap_strategy_context

logger = logging.getLogger(__name__)

# Initialize bootstrap context once per Lambda container
_bootstrap_context = None


def _get_bootstrap_context():
    """Get or initialize bootstrap context (container-level caching)."""
    global _bootstrap_context
    if _bootstrap_context is None:
        _bootstrap_context = bootstrap_strategy_context()
    return _bootstrap_context


def handler(event: dict, context: Any) -> dict[str, Any]:
    """AWS Lambda handler for strategy signal generation.
    
    Expected event format (CloudWatch Events):
    {
        "source": "aws.events",
        "detail-type": "Scheduled Event",
        "detail": {
            "symbols": ["AAPL", "MSFT", "GOOGL"]  # optional, defaults from config
        }
    }
    
    Args:
        event: AWS Lambda event (CloudWatch Events/EventBridge)
        context: AWS Lambda context object
        
    Returns:
        dict with processing status and metrics

    """
    correlation_id = getattr(context, "aws_request_id", "unknown")
    logger.info("Strategy signal handler invoked", extra={
        "correlation_id": correlation_id,
        "event_source": event.get("source", "unknown")
    })
    
    try:
        # Get dependencies
        bootstrap_ctx = _get_bootstrap_context()
        
        # Extract symbols from event or use defaults
        symbols_data = event.get("detail", {}).get("symbols", [])
        if not symbols_data:
            # Use default symbols from configuration
            symbols_data = list(bootstrap_ctx.config.strategy.default_strategy_allocations.keys())
        
        # Convert to Symbol value objects
        symbols = [Symbol(symbol_str) for symbol_str in symbols_data]
        
        logger.info("Generating signals", extra={
            "symbol_count": len(symbols),
            "symbols": symbols_data
        })
        
        # Execute use case
        published_signals = bootstrap_ctx.generate_signals_use_case.execute(symbols)
        
        # Build response
        result = {
            "status": "success",
            "processed": len(symbols),
            "signals_generated": len(published_signals),
            "correlation_id": correlation_id,
            "symbols": symbols_data,
            "signal_ids": [str(signal.message_id) for signal in published_signals]
        }
        
        logger.info("Strategy signal generation completed", extra={
            "correlation_id": correlation_id,
            "symbols_processed": len(symbols),
            "signals_generated": len(published_signals)
        })
        
        return result
        
    except (DataAccessError, SymbolNotFoundError) as e:
        # Domain/application errors - log and re-raise for DLQ handling
        logger.error(
            "Strategy signal generation failed: %s", 
            str(e),
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
                "component": "strategy_signal_handler"
            },
            exc_info=True
        )
        raise
        
    except PublishError as e:
        # Signal publishing failed - log and re-raise for retry
        logger.error(
            "Signal publishing failed: %s",
            str(e),
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
                "component": "strategy_signal_handler"
            },
            exc_info=True
        )
        raise
        
    except ConfigurationError as e:
        # Configuration issues - log and re-raise (likely permanent failure)
        logger.error(
            "Strategy context configuration error: %s",
            str(e),
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
                "component": "strategy_signal_handler"
            },
            exc_info=True
        )
        raise
        
    except Exception as e:
        # Unexpected error - log and re-raise
        logger.error(
            "Unexpected error in strategy signal handler: %s",
            str(e),
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
                "component": "strategy_signal_handler"
            },
            exc_info=True
        )
        raise