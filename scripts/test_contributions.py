#!/usr/bin/env python3
"""Test script for strategy_contributions roundtrip."""
import _setup_imports  # noqa: F401

from decimal import Decimal
from datetime import UTC, datetime
from the_alchemiser.shared.schemas.consolidated_portfolio import ConsolidatedPortfolio

# Create a portfolio with strategy contributions
portfolio = ConsolidatedPortfolio(
    target_allocations={'AAPL': Decimal('0.5'), 'SPY': Decimal('0.5')},
    strategy_contributions={
        'momentum': {'AAPL': Decimal('0.3'), 'SPY': Decimal('0.2')},
        'mean_rev': {'AAPL': Decimal('0.2'), 'SPY': Decimal('0.3')},
    },
    correlation_id='test-123',
    timestamp=datetime.now(UTC),
    strategy_count=2,
    source_strategies=['momentum', 'mean_rev'],
)

# Serialize like the aggregator does
event_data = {
    'target_allocations': {k: str(v) for k, v in portfolio.target_allocations.items()},
    'strategy_contributions': {
        strategy: {symbol: str(weight) for symbol, weight in allocations.items()}
        for strategy, allocations in portfolio.strategy_contributions.items()
    },
    'correlation_id': portfolio.correlation_id,
    'timestamp': portfolio.timestamp.isoformat(),
    'strategy_count': portfolio.strategy_count,
    'source_strategies': portfolio.source_strategies,
    'schema_version': portfolio.schema_version,
    'is_partial': portfolio.is_partial,
}

print("Event data:", event_data)

# Deserialize like Portfolio Lambda does
restored = ConsolidatedPortfolio.from_json_dict(event_data)

print('Original contributions:', portfolio.strategy_contributions)
print('Restored contributions:', restored.strategy_contributions)
print('Match:', portfolio.strategy_contributions == restored.strategy_contributions)
