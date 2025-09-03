# Comprehensive Legacy & Deprecation Audit Report

**Generated**: 2025-09-03 16:31:45
**Total Findings**: 271

## Executive Summary

This comprehensive audit identified **271 items** requiring attention:

- **Legacy**: 110 items
- **Deprecated**: 36 items
- **Shim**: 125 items

## Risk Level Distribution

- **HIGH RISK**: 27 items - Require immediate attention
- **MEDIUM RISK**: 185 items - Should be addressed soon
- **LOW RISK**: 59 items - Can be addressed as time permits

## Detailed Findings

### HIGH RISK ITEMS (27 items)

#### Legacy Items

| File Path | Description | Suggested Action | Line |
|-----------|-------------|------------------|------|
| `the_alchemiser/execution/services/__init__.py` | File in legacy DDD structure: services/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/utils/__init__.py` | File in legacy DDD structure: utils/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/utils/serialization.py` | File in legacy DDD structure: utils/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/shared/utils/error_reporter.py` | File in legacy DDD structure: utils/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/shared/utils/account_utils.py` | File in legacy DDD structure: utils/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/shared/utils/error_recovery.py` | File in legacy DDD structure: utils/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/shared/utils/error_monitoring.py` | File in legacy DDD structure: utils/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/shared/utils/retry_decorator.py` | File in legacy DDD structure: utils/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/shared/utils/__init__.py` | File in legacy DDD structure: utils/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/shared/utils/cache_manager.py` | File in legacy DDD structure: utils/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/shared/utils/config.py` | File in legacy DDD structure: utils/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/shared/utils/context.py` | File in legacy DDD structure: utils/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/shared/utils/s3_utils.py` | File in legacy DDD structure: utils/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/shared/utils/error_scope.py` | File in legacy DDD structure: utils/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/shared/utils/service_factory.py` | File in legacy DDD structure: utils/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/shared/utils/error_handling.py` | File in legacy DDD structure: utils/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/shared/utils/common.py` | File in legacy DDD structure: utils/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/shared/utils/decorators.py` | File in legacy DDD structure: utils/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/shared/services/tick_size_service.py` | File in legacy DDD structure: services/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/shared/services/websocket_connection_manager.py` | File in legacy DDD structure: services/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/shared/services/real_time_pricing.py` | File in legacy DDD structure: services/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/shared/services/alert_service.py` | File in legacy DDD structure: services/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/shared/services/__init__.py` | File in legacy DDD structure: services/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/portfolio/utils/portfolio_utilities.py` | File in legacy DDD structure: utils/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/portfolio/utils/__init__.py` | File in legacy DDD structure: utils/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py` | File in legacy DDD structure: utils/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |
| `the_alchemiser/portfolio/services/__init__.py` | File in legacy DDD structure: services/ | Migrate to new modular structure (strategy/portfolio/execution/shared) | - |

### MEDIUM RISK ITEMS (185 items)

#### Legacy Items

| File Path | Description | Suggested Action | Line |
|-----------|-------------|------------------|------|
| `the_alchemiser/execution/orders/service.py` | Legacy import pattern: from the_alchemiser.shared.utils.decorators import translate_trading_errors | Update import to use new modular structure | 30 |
| `the_alchemiser/execution/core/manager.py` | Legacy import pattern: from the_alchemiser.shared.services.errors import handle_errors_with_retry | Update import to use new modular structure | 16 |
| `the_alchemiser/execution/core/execution_manager.py` | Legacy import pattern: from the_alchemiser.shared.utils.decorators import translate_trading_errors | Update import to use new modular structure | 102 |
| `the_alchemiser/execution/core/account_facade.py` | Legacy import pattern: from the_alchemiser.utils.serialization import ensure_serialized_dict | Update import to use new modular structure | 51 |
| `the_alchemiser/execution/brokers/alpaca_client.py` | Legacy import pattern: from the_alchemiser.shared.services.websocket_connection_manager import ( | Update import to use new modular structure | 84 |
| `the_alchemiser/execution/strategies/repeg_strategy.py` | Legacy import pattern: from the_alchemiser.shared.services.tick_size_service import ( | Update import to use new modular structure | 19 |
| `the_alchemiser/utils/__init__.py` | Legacy import pattern: # from the_alchemiser.shared.services.price_utils import format_price | Update import to use new modular structure | 14 |
| `the_alchemiser/strategy/engines/klm_ensemble_engine.py` | Legacy import pattern: from the_alchemiser.shared.utils.common import ActionType | Update import to use new modular structure | 28 |
| `the_alchemiser/strategy/engines/klm_workers/variant_530_18.py` | Legacy import pattern: from the_alchemiser.shared.utils.common import ActionType | Update import to use new modular structure | 24 |
| `the_alchemiser/strategy/engines/klm_workers/variant_506_38.py` | Legacy import pattern: from the_alchemiser.shared.utils.common import ActionType | Update import to use new modular structure | 21 |
| `the_alchemiser/strategy/engines/klm_workers/variant_410_38.py` | Legacy import pattern: from the_alchemiser.shared.utils.common import ActionType | Update import to use new modular structure | 14 |
| `the_alchemiser/strategy/engines/klm_workers/variant_830_21.py` | Legacy import pattern: from the_alchemiser.shared.utils.common import ActionType | Update import to use new modular structure | 17 |
| `the_alchemiser/strategy/engines/klm_workers/variant_nova.py` | Legacy import pattern: from the_alchemiser.shared.utils.common import ActionType | Update import to use new modular structure | 18 |
| `the_alchemiser/strategy/engines/klm_workers/variant_1280_26.py` | Legacy import pattern: from the_alchemiser.shared.utils.common import ActionType | Update import to use new modular structure | 19 |
| `the_alchemiser/strategy/engines/klm_workers/variant_520_22.py` | Legacy import pattern: from the_alchemiser.shared.utils.common import ActionType | Update import to use new modular structure | 17 |
| `the_alchemiser/strategy/engines/klm_workers/base_klm_variant.py` | Legacy import pattern: from the_alchemiser.shared.utils.common import ActionType | Update import to use new modular structure | 18 |
| `the_alchemiser/strategy/engines/klm_workers/variant_1200_28.py` | Legacy import pattern: from the_alchemiser.shared.utils.common import ActionType | Update import to use new modular structure | 17 |
| `the_alchemiser/strategy/engines/tecl_strategy_engine.py` | Legacy import pattern: from the_alchemiser.shared.utils.common import ActionType | Update import to use new modular structure | 37 |
| `the_alchemiser/strategy/engines/core/trading_engine.py` | Legacy import pattern: from the_alchemiser.shared.utils.context import create_error_context | Update import to use new modular structure | 73 |
| `the_alchemiser/strategy/engines/core/trading_engine.py` | Legacy import pattern: from the_alchemiser.shared.utils.context import ( | Update import to use new modular structure | 415 |
| `the_alchemiser/strategy/engines/core/trading_engine.py` | Legacy import pattern: from the_alchemiser.shared.services.errors import handle_trading_error | Update import to use new modular structure | 726 |
| `the_alchemiser/strategy/engines/typed_klm_ensemble_engine.py` | Legacy import pattern: from the_alchemiser.shared.utils.common import ActionType | Update import to use new modular structure | 28 |
| `the_alchemiser/strategy/data/market_data_service.py` | Legacy import pattern: from the_alchemiser.shared.utils.decorators import translate_market_data_errors | Update import to use new modular structure | 30 |
| `the_alchemiser/main.py` | Legacy import pattern: from the_alchemiser.shared.utils.service_factory import ServiceFactory | Update import to use new modular structure | 41 |
| `the_alchemiser/lambda_handler.py` | Legacy import pattern: from the_alchemiser.shared.services.errors import ( | Update import to use new modular structure | 259 |
| `the_alchemiser/lambda_handler.py` | Legacy import pattern: from the_alchemiser.shared.services.errors import ( | Update import to use new modular structure | 307 |
| `the_alchemiser/shared/utils/cache_manager.py` | Legacy import pattern: from the_alchemiser.shared.services.shared.config_service import ConfigService | Update import to use new modular structure | 16 |
| `the_alchemiser/shared/services/alert_service.py` | Legacy import pattern: from the_alchemiser.shared.utils.s3_utils import get_s3_handler | Update import to use new modular structure | 218 |
| `the_alchemiser/shared/config/service_providers.py` | Legacy import pattern: from the_alchemiser.portfolio.services.position_service import PositionService | Update import to use new modular structure | 13 |
| `the_alchemiser/shared/config/bootstrap.py` | Legacy import pattern: from the_alchemiser.shared.utils.context import create_error_context | Update import to use new modular structure | 25 |
| `the_alchemiser/shared/cli/cli.py` | Legacy import pattern: # from the_alchemiser.execution.services.trading_service_manager import TradingServiceManager | Update import to use new modular structure | 53 |
| `the_alchemiser/shared/cli/portfolio_calculations.py` | Legacy import pattern: from the_alchemiser.shared.utils.account_utils import ( | Update import to use new modular structure | 19 |
| `the_alchemiser/shared/notifications/templates/portfolio.py` | Legacy import pattern: from the_alchemiser.shared.utils.account_utils import ( | Update import to use new modular structure | 440 |
| `the_alchemiser/shared/math/trading_math.py` | Legacy import pattern: from the_alchemiser.shared.services.tick_size_service import ( | Update import to use new modular structure | 171 |
| `the_alchemiser/shared/reporting/reporting.py` | Legacy import pattern: from the_alchemiser.portfolio.utils.portfolio_pnl_utils import ( | Update import to use new modular structure | 27 |
| `the_alchemiser/shared/reporting/reporting.py` | Legacy import pattern: from the_alchemiser.shared.utils.s3_utils import get_s3_handler | Update import to use new modular structure | 81 |
| `the_alchemiser/shared/reporting/reporting.py` | Legacy import pattern: from the_alchemiser.shared.utils.account_utils import ( | Update import to use new modular structure | 130 |
| `the_alchemiser/shared/logging/logging_utils.py` | Legacy import pattern: from the_alchemiser.shared.utils.s3_utils import S3FileHandler | Update import to use new modular structure | 18 |
| `the_alchemiser/portfolio/execution/execution_service.py` | Legacy import pattern: "Importing from 'the_alchemiser.application.portfolio.services.rebalance_execution_service' is deprecated. " | Update import to use new modular structure | 8 |
| `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py` | Legacy import pattern: "Importing from 'the_alchemiser.application.portfolio.portfolio_pnl_utils' is deprecated. " | Update import to use new modular structure | 9 |
| `the_alchemiser/portfolio/pnl/strategy_order_tracker.py` | Legacy import pattern: from the_alchemiser.shared.services.errors import TradingSystemErrorHandler | Update import to use new modular structure | 44 |
| `the_alchemiser/portfolio/pnl/strategy_order_tracker.py` | Legacy import pattern: from the_alchemiser.shared.utils.s3_utils import get_s3_handler | Update import to use new modular structure | 49 |
| `the_alchemiser/portfolio/holdings/position_service.py` | Legacy import pattern: from the_alchemiser.shared.utils.decorators import translate_trading_errors | Update import to use new modular structure | 28 |
| `the_alchemiser/portfolio/rebalancing/rebalance_plan.py` | Legacy import pattern: "Importing from 'the_alchemiser.domain.portfolio.rebalancing.rebalance_plan' is deprecated. " | Update import to use new modular structure | 8 |
| `the_alchemiser/portfolio/rebalancing/orchestrator.py` | Legacy import pattern: "Importing from 'the_alchemiser.application.portfolio.rebalancing_orchestrator' is deprecated. " | Update import to use new modular structure | 8 |
| `the_alchemiser/portfolio/rebalancing/rebalancing_service.py` | Legacy import pattern: "Importing from 'the_alchemiser.application.portfolio.services.portfolio_rebalancing_service' is deprecated. " | Update import to use new modular structure | 8 |
| `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py` | Legacy import pattern: "Importing from 'the_alchemiser.application.portfolio.rebalancing_orchestrator_facade' is deprecated. " | Update import to use new modular structure | 8 |
| `the_alchemiser/portfolio/calculations/portfolio_calculations.py` | Legacy import pattern: from the_alchemiser.shared.utils.account_utils import ( | Update import to use new modular structure | 14 |
| `the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py` | Legacy import pattern: from the_alchemiser.portfolio.utils.portfolio_utilities import PortfolioUtilities | Update import to use new modular structure | 20 |
| `the_alchemiser/portfolio/core/portfolio_management_facade.py` | Legacy import pattern: from the_alchemiser.utils.serialization import ensure_serialized_dict | Update import to use new modular structure | 31 |
| `the_alchemiser/portfolio/core/portfolio_analysis_service.py` | Legacy import pattern: from the_alchemiser.portfolio.utils.portfolio_utilities import PortfolioUtilities | Update import to use new modular structure | 14 |
| `the_alchemiser/portfolio/core/rebalancing_orchestrator_facade.py` | Legacy import pattern: from the_alchemiser.shared.utils.context import create_error_context | Update import to use new modular structure | 22 |
| `the_alchemiser/portfolio/analytics/analysis_service.py` | Legacy import pattern: "Importing from 'the_alchemiser.application.portfolio.services.portfolio_analysis_service' is deprecated. " | Update import to use new modular structure | 8 |
| `the_alchemiser/portfolio/analytics/position_analyzer.py` | Legacy import pattern: "Importing from 'the_alchemiser.domain.portfolio.position.position_analyzer' is deprecated. " | Update import to use new modular structure | 8 |
| `the_alchemiser/portfolio/analytics/position_delta.py` | Legacy import pattern: "Importing from 'the_alchemiser.domain.portfolio.position.position_delta' is deprecated. " | Update import to use new modular structure | 8 |
| `the_alchemiser/portfolio/analytics/attribution_engine.py` | Legacy import pattern: "Importing from 'the_alchemiser.domain.portfolio.strategy_attribution.attribution_engine' is deprecated. " | Update import to use new modular structure | 8 |
| `the_alchemiser/portfolio/positions/position_service.py` | Legacy import pattern: "Importing from 'the_alchemiser.services.trading.position_service' is deprecated. " | Update import to use new modular structure | 8 |
| `the_alchemiser/portfolio/positions/legacy_position_manager.py` | Legacy import pattern: "Importing from 'the_alchemiser.services.trading.position_manager' is deprecated. " | Update import to use new modular structure | 8 |

#### Shim Items

| File Path | Description | Suggested Action | Line |
|-----------|-------------|------------------|------|
| `the_alchemiser/execution/orders/asset_order_handler.py` | Compatibility shim detected: This method remains for backward compatibility only. | Migrate imports and remove shim | 169 |
| `the_alchemiser/execution/orders/asset_order_handler.py` | Compatibility shim detected: import warnings | Migrate imports and remove shim | 181 |
| `the_alchemiser/execution/orders/asset_order_handler.py` | Compatibility shim detected: DeprecationWarning, | Migrate imports and remove shim | 186 |
| `the_alchemiser/execution/orders/asset_order_handler.py` | Compatibility shim detected: This method remains for backward compatibility only. | Migrate imports and remove shim | 293 |
| `the_alchemiser/execution/orders/asset_order_handler.py` | Compatibility shim detected: import warnings | Migrate imports and remove shim | 305 |
| `the_alchemiser/execution/orders/asset_order_handler.py` | Compatibility shim detected: DeprecationWarning, | Migrate imports and remove shim | 310 |
| `the_alchemiser/execution/core/execution_manager_legacy.py` | Compatibility shim detected: CRITICAL: This module has moved to the_alchemiser.execution.core | Migrate imports and remove shim | 3 |
| `the_alchemiser/execution/core/execution_manager_legacy.py` | Compatibility shim detected: This shim maintains backward compatibility for execution systems. | Migrate imports and remove shim | 4 |
| `the_alchemiser/execution/core/execution_manager_legacy.py` | Compatibility shim detected: logging.getLogger(__name__).info("Import redirected from legacy path to execution.core module") | Migrate imports and remove shim | 13 |
| `the_alchemiser/execution/core/execution_manager_legacy.py` | Star import compatibility shim | Replace with direct imports and remove shim | - |
| `the_alchemiser/execution/core/execution_schemas.py` | Compatibility shim detected: # Backward compatibility aliases | Migrate imports and remove shim | 199 |
| `the_alchemiser/execution/core/execution_schemas.py` | Compatibility shim detected: # Backward compatibility aliases - will be removed in future version | Migrate imports and remove shim | 209 |
| `the_alchemiser/execution/core/canonical_executor.py` | Compatibility shim detected: CRITICAL: This module has moved to the_alchemiser.execution.core | Migrate imports and remove shim | 3 |
| `the_alchemiser/execution/core/canonical_executor.py` | Compatibility shim detected: This shim maintains backward compatibility for execution systems. | Migrate imports and remove shim | 4 |
| `the_alchemiser/execution/core/canonical_executor.py` | Compatibility shim detected: logging.getLogger(__name__).info("Import redirected from legacy path to execution.core module") | Migrate imports and remove shim | 13 |
| `the_alchemiser/execution/core/canonical_executor.py` | Star import compatibility shim | Replace with direct imports and remove shim | - |
| `the_alchemiser/execution/mappers/orders.py` | Compatibility shim detected: """Convert ValidatedOrderDTO back to dictionary for backward compatibility. | Migrate imports and remove shim | 167 |
| `the_alchemiser/execution/brokers/alpaca_client.py` | Compatibility shim detected: trading_client: Alpaca trading client for API calls (backward compatibility). | Migrate imports and remove shim | 102 |
| `the_alchemiser/execution/brokers/alpaca_client.py` | Compatibility shim detected: self.trading_client = alpaca_manager.trading_client  # Backward compatibility | Migrate imports and remove shim | 130 |
| `the_alchemiser/strategy/signals/strategy_signal.py` | Compatibility shim detected: This module provides backward compatibility. | Migrate imports and remove shim | 3 |
| `the_alchemiser/strategy/signals/strategy_signal.py` | Compatibility shim detected: import warnings | Migrate imports and remove shim | 6 |
| `the_alchemiser/strategy/signals/strategy_signal.py` | Compatibility shim detected: DeprecationWarning, | Migrate imports and remove shim | 13 |
| `the_alchemiser/strategy/signals/strategy_signal.py` | Star import compatibility shim | Replace with direct imports and remove shim | - |
| `the_alchemiser/main.py` | Compatibility shim detected: )  # Keep global for backward compatibility during transition | Migrate imports and remove shim | 73 |
| `the_alchemiser/shared/utils/__init__.py` | Star import compatibility shim | Replace with direct imports and remove shim | - |
| `the_alchemiser/shared/utils/error_handling.py` | Compatibility shim detected: This module is kept temporarily for backward compatibility but will be removed | Migrate imports and remove shim | 10 |
| `the_alchemiser/shared/utils/error_handling.py` | Compatibility shim detected: import warnings | Migrate imports and remove shim | 16 |
| `the_alchemiser/shared/utils/error_handling.py` | Compatibility shim detected: DeprecationWarning, | Migrate imports and remove shim | 24 |
| `the_alchemiser/shared/utils/error_handling.py` | Compatibility shim detected: DeprecationWarning, | Migrate imports and remove shim | 38 |
| `the_alchemiser/shared/utils/error_handling.py` | Compatibility shim detected: raise DeprecationWarning( | Migrate imports and remove shim | 52 |
| `the_alchemiser/shared/utils/error_handling.py` | Compatibility shim detected: raise DeprecationWarning( | Migrate imports and remove shim | 73 |
| `the_alchemiser/shared/utils/error_handling.py` | Compatibility shim detected: raise DeprecationWarning( | Migrate imports and remove shim | 82 |
| `the_alchemiser/shared/utils/error_handling.py` | Compatibility shim detected: raise DeprecationWarning("ErrorContext is deprecated. Use ErrorScope instead.") | Migrate imports and remove shim | 92 |
| `the_alchemiser/shared/utils/error_handling.py` | Compatibility shim detected: raise DeprecationWarning(f"{name} is deprecated and has been removed.") | Migrate imports and remove shim | 101 |
| `the_alchemiser/shared/utils/error_handling.py` | Compatibility shim detected: raise DeprecationWarning( | Migrate imports and remove shim | 111 |
| `the_alchemiser/shared/value_objects/core_types.py` | Compatibility shim detected: # Legacy field aliases for backward compatibility | Migrate imports and remove shim | 100 |
| `the_alchemiser/shared/value_objects/core_types.py` | Compatibility shim detected: # Import for backward compatibility | Migrate imports and remove shim | 130 |
| `the_alchemiser/shared/value_objects/core_types.py` | Compatibility shim detected: # Import for backward compatibility | Migrate imports and remove shim | 134 |
| `the_alchemiser/shared/value_objects/core_types.py` | Compatibility shim detected: # Import for backward compatibility | Migrate imports and remove shim | 138 |
| `the_alchemiser/shared/value_objects/core_types.py` | Compatibility shim detected: # Import for backward compatibility | Migrate imports and remove shim | 149 |
| `the_alchemiser/shared/value_objects/core_types.py` | Compatibility shim detected: # Import for backward compatibility | Migrate imports and remove shim | 196 |
| `the_alchemiser/shared/value_objects/core_types.py` | Compatibility shim detected: # Import for backward compatibility | Migrate imports and remove shim | 229 |
| `the_alchemiser/shared/value_objects/core_types.py` | Compatibility shim detected: # Import for backward compatibility | Migrate imports and remove shim | 233 |
| `the_alchemiser/shared/value_objects/core_types.py` | Compatibility shim detected: # Import for backward compatibility | Migrate imports and remove shim | 237 |
| `the_alchemiser/shared/value_objects/core_types.py` | Compatibility shim detected: # Import for backward compatibility | Migrate imports and remove shim | 241 |
| `the_alchemiser/shared/value_objects/core_types.py` | Compatibility shim detected: # Import for backward compatibility | Migrate imports and remove shim | 270 |
| `the_alchemiser/shared/schemas/base.py` | Compatibility shim detected: # Backward compatibility alias - will be removed in future version | Migrate imports and remove shim | 28 |
| `the_alchemiser/portfolio/execution/execution_service.py` | Compatibility shim detected: """DEPRECATED: This module has moved to the_alchemiser.portfolio.allocation | Migrate imports and remove shim | 1 |
| `the_alchemiser/portfolio/execution/execution_service.py` | Compatibility shim detected: This shim maintains backward compatibility. | Migrate imports and remove shim | 2 |
| `the_alchemiser/portfolio/execution/execution_service.py` | Compatibility shim detected: import warnings | Migrate imports and remove shim | 5 |
| `the_alchemiser/portfolio/execution/execution_service.py` | Compatibility shim detected: DeprecationWarning, | Migrate imports and remove shim | 10 |
| `the_alchemiser/portfolio/execution/execution_service.py` | Compatibility shim detected: # Import all symbols from the new location | Migrate imports and remove shim | 14 |
| `the_alchemiser/portfolio/execution/execution_service.py` | Star import compatibility shim | Replace with direct imports and remove shim | - |
| `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py` | Compatibility shim detected: """DEPRECATED: This module has moved to the_alchemiser.portfolio.pnl | Migrate imports and remove shim | 2 |
| `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py` | Compatibility shim detected: This shim maintains backward compatibility. | Migrate imports and remove shim | 3 |
| `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py` | Compatibility shim detected: import warnings | Migrate imports and remove shim | 6 |
| `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py` | Compatibility shim detected: DeprecationWarning, | Migrate imports and remove shim | 11 |
| `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py` | Compatibility shim detected: # Import all symbols from the new location | Migrate imports and remove shim | 15 |
| `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py` | Star import compatibility shim | Replace with direct imports and remove shim | - |
| `the_alchemiser/portfolio/holdings/position_manager.py` | Compatibility shim detected: This method remains for backward compatibility only. | Migrate imports and remove shim | 91 |
| `the_alchemiser/portfolio/holdings/position_manager.py` | Compatibility shim detected: import warnings | Migrate imports and remove shim | 102 |
| `the_alchemiser/portfolio/holdings/position_manager.py` | Compatibility shim detected: DeprecationWarning, | Migrate imports and remove shim | 107 |
| `the_alchemiser/portfolio/holdings/position_manager.py` | Compatibility shim detected: This method remains for backward compatibility only. | Migrate imports and remove shim | 149 |
| `the_alchemiser/portfolio/holdings/position_manager.py` | Compatibility shim detected: import warnings | Migrate imports and remove shim | 159 |
| `the_alchemiser/portfolio/holdings/position_manager.py` | Compatibility shim detected: DeprecationWarning, | Migrate imports and remove shim | 164 |
| `the_alchemiser/portfolio/rebalancing/rebalance_plan.py` | Compatibility shim detected: """DEPRECATED: This module has moved to the_alchemiser.portfolio.allocation | Migrate imports and remove shim | 1 |
| `the_alchemiser/portfolio/rebalancing/rebalance_plan.py` | Compatibility shim detected: This shim maintains backward compatibility. | Migrate imports and remove shim | 2 |
| `the_alchemiser/portfolio/rebalancing/rebalance_plan.py` | Compatibility shim detected: import warnings | Migrate imports and remove shim | 5 |
| `the_alchemiser/portfolio/rebalancing/rebalance_plan.py` | Compatibility shim detected: DeprecationWarning, | Migrate imports and remove shim | 10 |
| `the_alchemiser/portfolio/rebalancing/rebalance_plan.py` | Compatibility shim detected: # Import all symbols from the new location | Migrate imports and remove shim | 14 |
| `the_alchemiser/portfolio/rebalancing/rebalance_plan.py` | Star import compatibility shim | Replace with direct imports and remove shim | - |
| `the_alchemiser/portfolio/rebalancing/orchestrator.py` | Compatibility shim detected: """DEPRECATED: This module has moved to the_alchemiser.portfolio.core | Migrate imports and remove shim | 1 |
| `the_alchemiser/portfolio/rebalancing/orchestrator.py` | Compatibility shim detected: This shim maintains backward compatibility. | Migrate imports and remove shim | 2 |
| `the_alchemiser/portfolio/rebalancing/orchestrator.py` | Compatibility shim detected: import warnings | Migrate imports and remove shim | 5 |
| `the_alchemiser/portfolio/rebalancing/orchestrator.py` | Compatibility shim detected: DeprecationWarning, | Migrate imports and remove shim | 10 |
| `the_alchemiser/portfolio/rebalancing/orchestrator.py` | Compatibility shim detected: # Import all symbols from the new location | Migrate imports and remove shim | 14 |
| `the_alchemiser/portfolio/rebalancing/orchestrator.py` | Star import compatibility shim | Replace with direct imports and remove shim | - |
| `the_alchemiser/portfolio/rebalancing/rebalancing_service.py` | Compatibility shim detected: """DEPRECATED: This module has moved to the_alchemiser.portfolio.allocation | Migrate imports and remove shim | 1 |
| `the_alchemiser/portfolio/rebalancing/rebalancing_service.py` | Compatibility shim detected: This shim maintains backward compatibility. | Migrate imports and remove shim | 2 |
| `the_alchemiser/portfolio/rebalancing/rebalancing_service.py` | Compatibility shim detected: import warnings | Migrate imports and remove shim | 5 |
| `the_alchemiser/portfolio/rebalancing/rebalancing_service.py` | Compatibility shim detected: DeprecationWarning, | Migrate imports and remove shim | 10 |
| `the_alchemiser/portfolio/rebalancing/rebalancing_service.py` | Compatibility shim detected: # Import all symbols from the new location | Migrate imports and remove shim | 14 |
| `the_alchemiser/portfolio/rebalancing/rebalancing_service.py` | Star import compatibility shim | Replace with direct imports and remove shim | - |
| `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py` | Compatibility shim detected: """DEPRECATED: This module has moved to the_alchemiser.portfolio.core | Migrate imports and remove shim | 1 |
| `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py` | Compatibility shim detected: This shim maintains backward compatibility. | Migrate imports and remove shim | 2 |
| `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py` | Compatibility shim detected: import warnings | Migrate imports and remove shim | 5 |
| `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py` | Compatibility shim detected: DeprecationWarning, | Migrate imports and remove shim | 10 |
| `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py` | Compatibility shim detected: # Import all symbols from the new location | Migrate imports and remove shim | 14 |
| `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py` | Star import compatibility shim | Replace with direct imports and remove shim | - |
| `the_alchemiser/portfolio/analytics/analysis_service.py` | Compatibility shim detected: """DEPRECATED: This module has moved to the_alchemiser.portfolio.core | Migrate imports and remove shim | 1 |
| `the_alchemiser/portfolio/analytics/analysis_service.py` | Compatibility shim detected: This shim maintains backward compatibility. | Migrate imports and remove shim | 2 |
| `the_alchemiser/portfolio/analytics/analysis_service.py` | Compatibility shim detected: import warnings | Migrate imports and remove shim | 5 |
| `the_alchemiser/portfolio/analytics/analysis_service.py` | Compatibility shim detected: DeprecationWarning, | Migrate imports and remove shim | 10 |
| `the_alchemiser/portfolio/analytics/analysis_service.py` | Compatibility shim detected: # Import all symbols from the new location | Migrate imports and remove shim | 14 |
| `the_alchemiser/portfolio/analytics/analysis_service.py` | Star import compatibility shim | Replace with direct imports and remove shim | - |
| `the_alchemiser/portfolio/analytics/position_analyzer.py` | Compatibility shim detected: """DEPRECATED: This module has moved to the_alchemiser.portfolio.holdings | Migrate imports and remove shim | 1 |
| `the_alchemiser/portfolio/analytics/position_analyzer.py` | Compatibility shim detected: This shim maintains backward compatibility. | Migrate imports and remove shim | 2 |
| `the_alchemiser/portfolio/analytics/position_analyzer.py` | Compatibility shim detected: import warnings | Migrate imports and remove shim | 5 |
| `the_alchemiser/portfolio/analytics/position_analyzer.py` | Compatibility shim detected: DeprecationWarning, | Migrate imports and remove shim | 10 |
| `the_alchemiser/portfolio/analytics/position_analyzer.py` | Compatibility shim detected: # Import all symbols from the new location | Migrate imports and remove shim | 14 |
| `the_alchemiser/portfolio/analytics/position_analyzer.py` | Star import compatibility shim | Replace with direct imports and remove shim | - |
| `the_alchemiser/portfolio/analytics/position_delta.py` | Compatibility shim detected: """DEPRECATED: This module has moved to the_alchemiser.portfolio.holdings | Migrate imports and remove shim | 1 |
| `the_alchemiser/portfolio/analytics/position_delta.py` | Compatibility shim detected: This shim maintains backward compatibility. | Migrate imports and remove shim | 2 |
| `the_alchemiser/portfolio/analytics/position_delta.py` | Compatibility shim detected: import warnings | Migrate imports and remove shim | 5 |
| `the_alchemiser/portfolio/analytics/position_delta.py` | Compatibility shim detected: DeprecationWarning, | Migrate imports and remove shim | 10 |
| `the_alchemiser/portfolio/analytics/position_delta.py` | Compatibility shim detected: # Import all symbols from the new location | Migrate imports and remove shim | 14 |
| `the_alchemiser/portfolio/analytics/position_delta.py` | Star import compatibility shim | Replace with direct imports and remove shim | - |
| `the_alchemiser/portfolio/analytics/attribution_engine.py` | Compatibility shim detected: """DEPRECATED: This module has moved to the_alchemiser.portfolio.state | Migrate imports and remove shim | 1 |
| `the_alchemiser/portfolio/analytics/attribution_engine.py` | Compatibility shim detected: This shim maintains backward compatibility. | Migrate imports and remove shim | 2 |
| `the_alchemiser/portfolio/analytics/attribution_engine.py` | Compatibility shim detected: import warnings | Migrate imports and remove shim | 5 |
| `the_alchemiser/portfolio/analytics/attribution_engine.py` | Compatibility shim detected: DeprecationWarning, | Migrate imports and remove shim | 10 |
| `the_alchemiser/portfolio/analytics/attribution_engine.py` | Compatibility shim detected: # Import all symbols from the new location | Migrate imports and remove shim | 14 |
| `the_alchemiser/portfolio/analytics/attribution_engine.py` | Star import compatibility shim | Replace with direct imports and remove shim | - |
| `the_alchemiser/portfolio/positions/position_service.py` | Compatibility shim detected: """DEPRECATED: This module has moved to the_alchemiser.portfolio.holdings | Migrate imports and remove shim | 1 |
| `the_alchemiser/portfolio/positions/position_service.py` | Compatibility shim detected: This shim maintains backward compatibility. | Migrate imports and remove shim | 2 |
| `the_alchemiser/portfolio/positions/position_service.py` | Compatibility shim detected: import warnings | Migrate imports and remove shim | 5 |
| `the_alchemiser/portfolio/positions/position_service.py` | Compatibility shim detected: DeprecationWarning, | Migrate imports and remove shim | 10 |
| `the_alchemiser/portfolio/positions/position_service.py` | Compatibility shim detected: # Import all symbols from the new location | Migrate imports and remove shim | 14 |
| `the_alchemiser/portfolio/positions/position_service.py` | Star import compatibility shim | Replace with direct imports and remove shim | - |
| `the_alchemiser/portfolio/positions/legacy_position_manager.py` | Compatibility shim detected: """DEPRECATED: This module has moved to the_alchemiser.portfolio.holdings | Migrate imports and remove shim | 1 |
| `the_alchemiser/portfolio/positions/legacy_position_manager.py` | Compatibility shim detected: This shim maintains backward compatibility. | Migrate imports and remove shim | 2 |
| `the_alchemiser/portfolio/positions/legacy_position_manager.py` | Compatibility shim detected: import warnings | Migrate imports and remove shim | 5 |
| `the_alchemiser/portfolio/positions/legacy_position_manager.py` | Compatibility shim detected: DeprecationWarning, | Migrate imports and remove shim | 10 |
| `the_alchemiser/portfolio/positions/legacy_position_manager.py` | Compatibility shim detected: # Import all symbols from the new location | Migrate imports and remove shim | 14 |
| `the_alchemiser/portfolio/positions/legacy_position_manager.py` | Star import compatibility shim | Replace with direct imports and remove shim | - |

#### Deprecated Items

| File Path | Description | Suggested Action | Line |
|-----------|-------------|------------------|------|
| `the_alchemiser/execution/core/execution_manager_legacy.py` | Deprecated code or comment: """Business Unit: execution; Status: legacy. | Migrate to new modular structure | 1 |
| `the_alchemiser/execution/core/canonical_executor.py` | Deprecated code or comment: """Business Unit: execution; Status: legacy. | Migrate to new modular structure | 1 |

### LOW RISK ITEMS (59 items)

#### Deprecated Items

| File Path | Description | Suggested Action | Line |
|-----------|-------------|------------------|------|
| `the_alchemiser/execution/orders/service.py` | Deprecated code or comment: # Legacy place_market_order / place_limit_order removed. Use CanonicalOrderExecutor externally. | Review and remove if no longer needed | 79 |
| `the_alchemiser/execution/orders/validation.py` | Deprecated code or comment: # Legacy compatibility functions for existing code | Review and remove if no longer needed | 297 |
| `the_alchemiser/execution/orders/asset_order_handler.py` | Deprecated code or comment: DEPRECATED: This fractionability error handling has been moved to FractionabilityPolicy. | Replace with modern alternative | 167 |
| `the_alchemiser/execution/orders/asset_order_handler.py` | Deprecated code or comment: DEPRECATED: This fractionability error handling has been moved to FractionabilityPolicy. | Replace with modern alternative | 291 |
| `the_alchemiser/execution/brokers/alpaca_client.py` | Deprecated code or comment: # DEPRECATED: LimitOrderHandler import removed - use CanonicalOrderExecutor instead | Replace with modern alternative | 82 |
| `the_alchemiser/execution/brokers/alpaca_client.py` | Deprecated code or comment: # DEPRECATED: LimitOrderHandler removed - use CanonicalOrderExecutor instead | Replace with modern alternative | 143 |
| `the_alchemiser/execution/brokers/alpaca_client.py` | Deprecated code or comment: # Legacy direct order placement methods removed - use CanonicalOrderExecutor externally. | Review and remove if no longer needed | 223 |
| `the_alchemiser/strategy/data/domain_mapping.py` | Deprecated code or comment: # Legacy signal normalization (for backward compatibility) | Review and remove if no longer needed | 85 |
| `the_alchemiser/strategy/signals/strategy_signal.py` | Deprecated code or comment: """DEPRECATED: Strategy value objects moved to the_alchemiser.strategy.engines.value_objects. | Replace with modern alternative | 1 |
| `the_alchemiser/shared/utils/__init__.py` | Deprecated code or comment: from .error_handling import *  # Legacy deprecated | Replace with modern alternative | 21 |
| `the_alchemiser/shared/utils/error_handling.py` | Deprecated code or comment: # Deprecated stub functions that raise errors | Replace with modern alternative | 47 |
| `the_alchemiser/shared/utils/error_handling.py` | Deprecated code or comment: # Deprecated decorator stubs | Replace with modern alternative | 60 |
| `the_alchemiser/shared/utils/error_handling.py` | Deprecated code or comment: # Deprecated class stubs | Replace with modern alternative | 68 |
| `the_alchemiser/shared/utils/error_handling.py` | Deprecated code or comment: # Deprecated instances | Replace with modern alternative | 95 |
| `the_alchemiser/shared/cli/signal_display_utils.py` | Deprecated code or comment: # Legacy Alert objects path | Review and remove if no longer needed | 197 |
| `the_alchemiser/shared/cli/cli_formatter.py` | Deprecated code or comment: # Legacy numeric path | Review and remove if no longer needed | 319 |
| `the_alchemiser/shared/cli/cli.py` | Deprecated code or comment: # Legacy multi-strategy signal path ---------------------------------- | Review and remove if no longer needed | 356 |
| `the_alchemiser/shared/cli/trading_executor.py` | Deprecated code or comment: # Legacy dict case: Per No Legacy Fallback Policy, this path is | Review and remove if no longer needed | 344 |
| `the_alchemiser/shared/value_objects/core_types.py` | Deprecated code or comment: # Legacy field aliases for backward compatibility | Review and remove if no longer needed | 100 |
| `the_alchemiser/portfolio/execution/execution_service.py` | Deprecated code or comment: """DEPRECATED: This module has moved to the_alchemiser.portfolio.allocation | Replace with modern alternative | 1 |
| `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py` | Deprecated code or comment: """DEPRECATED: This module has moved to the_alchemiser.portfolio.pnl | Replace with modern alternative | 2 |
| `the_alchemiser/portfolio/holdings/position_manager.py` | Deprecated code or comment: DEPRECATED: This position validation logic has been moved to PositionPolicy. | Replace with modern alternative | 89 |
| `the_alchemiser/portfolio/holdings/position_manager.py` | Deprecated code or comment: DEPRECATED: This buying power validation logic has been moved to BuyingPowerPolicy. | Replace with modern alternative | 147 |
| `the_alchemiser/portfolio/rebalancing/rebalance_plan.py` | Deprecated code or comment: """DEPRECATED: This module has moved to the_alchemiser.portfolio.allocation | Replace with modern alternative | 1 |
| `the_alchemiser/portfolio/rebalancing/orchestrator.py` | Deprecated code or comment: """DEPRECATED: This module has moved to the_alchemiser.portfolio.core | Replace with modern alternative | 1 |
| `the_alchemiser/portfolio/rebalancing/rebalancing_service.py` | Deprecated code or comment: """DEPRECATED: This module has moved to the_alchemiser.portfolio.allocation | Replace with modern alternative | 1 |
| `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py` | Deprecated code or comment: """DEPRECATED: This module has moved to the_alchemiser.portfolio.core | Replace with modern alternative | 1 |
| `the_alchemiser/portfolio/analytics/analysis_service.py` | Deprecated code or comment: """DEPRECATED: This module has moved to the_alchemiser.portfolio.core | Replace with modern alternative | 1 |
| `the_alchemiser/portfolio/analytics/position_analyzer.py` | Deprecated code or comment: """DEPRECATED: This module has moved to the_alchemiser.portfolio.holdings | Replace with modern alternative | 1 |
| `the_alchemiser/portfolio/analytics/position_delta.py` | Deprecated code or comment: """DEPRECATED: This module has moved to the_alchemiser.portfolio.holdings | Replace with modern alternative | 1 |
| `the_alchemiser/portfolio/analytics/attribution_engine.py` | Deprecated code or comment: """DEPRECATED: This module has moved to the_alchemiser.portfolio.state | Replace with modern alternative | 1 |
| `the_alchemiser/portfolio/positions/position_service.py` | Deprecated code or comment: """DEPRECATED: This module has moved to the_alchemiser.portfolio.holdings | Replace with modern alternative | 1 |
| `the_alchemiser/portfolio/positions/legacy_position_manager.py` | Deprecated code or comment: """DEPRECATED: This module has moved to the_alchemiser.portfolio.holdings | Replace with modern alternative | 1 |
| `the_alchemiser/portfolio/state/symbol_classifier.py` | Deprecated code or comment: # Legacy nuclear and TECL symbols | Review and remove if no longer needed | 62 |

#### Legacy Items

| File Path | Description | Suggested Action | Line |
|-----------|-------------|------------------|------|
| `the_alchemiser/execution/orders/lifecycle_adapter.py` | File uses old naming convention: lifecycle_adapter.py | Consider renaming to match current conventions | - |
| `the_alchemiser/execution/core/account_facade.py` | File uses old naming convention: account_facade.py | Consider renaming to match current conventions | - |
| `the_alchemiser/execution/brokers/account_service.py` | File uses old naming convention: account_service.py | Consider renaming to match current conventions | - |
| `the_alchemiser/execution/strategies/execution_context_adapter.py` | File uses old naming convention: execution_context_adapter.py | Consider renaming to match current conventions | - |
| `the_alchemiser/strategy/data/streaming_service.py` | File uses old naming convention: streaming_service.py | Consider renaming to match current conventions | - |
| `the_alchemiser/strategy/data/price_service.py` | File uses old naming convention: price_service.py | Consider renaming to match current conventions | - |
| `the_alchemiser/strategy/data/market_data_service.py` | File uses old naming convention: market_data_service.py | Consider renaming to match current conventions | - |
| `the_alchemiser/strategy/data/strategy_market_data_service.py` | File uses old naming convention: strategy_market_data_service.py | Consider renaming to match current conventions | - |
| `the_alchemiser/strategy/data/shared_market_data_service.py` | File uses old naming convention: shared_market_data_service.py | Consider renaming to match current conventions | - |
| `the_alchemiser/strategy/mappers/market_data_adapter.py` | File uses old naming convention: market_data_adapter.py | Consider renaming to match current conventions | - |
| `the_alchemiser/shared/services/tick_size_service.py` | File uses old naming convention: tick_size_service.py | Consider renaming to match current conventions | - |
| `the_alchemiser/shared/services/alert_service.py` | File uses old naming convention: alert_service.py | Consider renaming to match current conventions | - |
| `the_alchemiser/shared/config/secrets_service.py` | File uses old naming convention: secrets_service.py | Consider renaming to match current conventions | - |
| `the_alchemiser/shared/config/config_service.py` | File uses old naming convention: config_service.py | Consider renaming to match current conventions | - |
| `the_alchemiser/portfolio/execution/execution_service.py` | File uses old naming convention: execution_service.py | Consider renaming to match current conventions | - |
| `the_alchemiser/portfolio/holdings/position_service.py` | File uses old naming convention: position_service.py | Consider renaming to match current conventions | - |
| `the_alchemiser/portfolio/rebalancing/rebalancing_service.py` | File uses old naming convention: rebalancing_service.py | Consider renaming to match current conventions | - |
| `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py` | File uses old naming convention: orchestrator_facade.py | Consider renaming to match current conventions | - |
| `the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py` | File uses old naming convention: portfolio_rebalancing_service.py | Consider renaming to match current conventions | - |
| `the_alchemiser/portfolio/allocation/rebalance_execution_service.py` | File uses old naming convention: rebalance_execution_service.py | Consider renaming to match current conventions | - |
| `the_alchemiser/portfolio/core/portfolio_management_facade.py` | File uses old naming convention: portfolio_management_facade.py | Consider renaming to match current conventions | - |
| `the_alchemiser/portfolio/core/portfolio_analysis_service.py` | File uses old naming convention: portfolio_analysis_service.py | Consider renaming to match current conventions | - |
| `the_alchemiser/portfolio/core/rebalancing_orchestrator_facade.py` | File uses old naming convention: rebalancing_orchestrator_facade.py | Consider renaming to match current conventions | - |
| `the_alchemiser/portfolio/analytics/analysis_service.py` | File uses old naming convention: analysis_service.py | Consider renaming to match current conventions | - |
| `the_alchemiser/portfolio/positions/position_service.py` | File uses old naming convention: position_service.py | Consider renaming to match current conventions | - |

## Recommendations

### Immediate Actions (High Risk)
1. **Legacy Structure Migration**: Migrate files from legacy DDD structure to new modular structure
2. **Deprecated Function Removal**: Remove functions marked with deprecated decorators
3. **Import Updates**: Update legacy import paths to new module structure

### Medium-Term Actions (Medium Risk)
1. **Shim Removal**: Update imports and remove compatibility shims
2. **Legacy Pattern Cleanup**: Replace old naming conventions and patterns
3. **Documentation Updates**: Update all references to old structure

### Low-Priority Actions (Low Risk)
1. **Backup File Cleanup**: Remove backup files that are no longer needed
2. **Comment Cleanup**: Remove TODO/FIXME comments for completed migrations
3. **Archive Review**: Review archived files for potential removal

## Implementation Strategy

1. **Phase 1**: Address all HIGH risk items first
2. **Phase 2**: Tackle MEDIUM risk items in batches
3. **Phase 3**: Clean up LOW risk items as time permits
4. **Testing**: Run full test suite after each phase
5. **Documentation**: Update all documentation to reflect changes

---
*Report generated by comprehensive_legacy_audit.py on 2025-09-03*