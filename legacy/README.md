# Legacy Code Archive

This directory contains legacy code that has been replaced by the modernized DDD architecture.

## Portfolio Rebalancer Refactoring (August 2025)

### Replaced Files

- `portfolio_rebalancer/portfolio_rebalancer_legacy.py` - Original monolithic portfolio rebalancer (620 lines)
- `portfolio_rebalancer/__init___legacy.py` - Legacy package initialization
- `main_original_backup.py` - Original main entry point backup

### New Architecture

The legacy portfolio rebalancer has been replaced with a modular Domain-Driven Design architecture:

#### New System Location: `the_alchemiser/application/portfolio/`
- **Domain Layer**: Core business logic and interfaces
- **Services Layer**: Business logic orchestration
- **Infrastructure Layer**: External integrations
- **Application Layer**: Workflow coordination

#### Key Components
- `PortfolioManagementFacade` - Main entry point
- `RebalanceExecutionService` - Trade execution
- `LegacyPortfolioRebalancerAdapter` - Backward compatibility bridge

### Migration Status

✅ **Complete**: New modular system is active in production
✅ **Backward Compatible**: Legacy adapter maintains existing interfaces
✅ **Type Safe**: 100% mypy compliance
✅ **Tested**: All components validated and working

### Usage

The new system is automatically used when:
- Running `poetry run alchemiser trade`
- Running `poetry run alchemiser signal`
- Deployed to AWS Lambda

Legacy fallback only occurs for direct `TradingEngine()` instantiation without dependency injection.

---

*Files archived on: August 14, 2025*
*Branch: portfolio-rebalancer-refactor*
*Pull Request: #61 - Modernize portfolio rebalancer with DDD architecture*
