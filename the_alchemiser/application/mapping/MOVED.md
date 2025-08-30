# MOVED: Mapping Layer Migration

This directory has been migrated to `anti_corruption/` as part of DDD Epic #375 Phase 7.

## New Locations:

- **Broker mappings**: `the_alchemiser/anti_corruption/brokers/`
  - Alpaca order mappings, account mappings, position mappings
  - Order status normalization, execution mappings

- **Market Data mappings**: `the_alchemiser/anti_corruption/market_data/`
  - Domain mappers, market data transformations
  - Strategy adapter mappings, pandas time series

- **Serialization mappings**: `the_alchemiser/anti_corruption/serialization/`
  - Policy DTO mappings, rebalance plan mappings
  - Strategy signal mappings, tracking mappings
  - Execution summary mappings

- **Version Upgrades**: `the_alchemiser/anti_corruption/upgrades/`
  - Future version-to-version upgrade pathways

## Import Changes:

Old:
```python
from the_alchemiser.application.mapping.alpaca_dto_mapping import ...
```

New:
```python
from the_alchemiser.anti_corruption.brokers.alpaca_dto_mapping import ...
```

All import statements across the codebase have been updated accordingly.