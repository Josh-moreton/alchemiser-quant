# Application Mapping

This package contains DTO ↔ Domain mappers and anti-corruption adapters for the Typed Domain V2 system.

## Current Modules

- **`order_mapping.py`** - Maps Alpaca order objects to domain Order entities
- **`account_mapping.py`** - Maps account data to typed AccountSummary structures  
- **`position_mapping.py`** - Maps position data to PositionSummary
- **`strategy_signal_mapping.py`** - Maps legacy signals to typed StrategySignal

## Key Principles

- Keep mappings explicit and tested
- Avoid importing infrastructure or frameworks here
- Use Decimal for all financial values
- Follow domain purity rules (no framework imports in domain objects)

## Comprehensive Documentation

For detailed guidance on mapping boundaries, domain purity rules, Decimal normalization, and anti-corruption patterns, see:

**[📖 Mapping Boundaries Documentation](../../docs/typing-migration/mapping-boundaries.md)**

This includes:
- Three mapping boundary patterns (DTO ↔ Domain ↔ Infra)
- Code examples and templates
- Domain purity enforcement
- No Legacy Fallback policy compliance
- Testing patterns and troubleshooting
