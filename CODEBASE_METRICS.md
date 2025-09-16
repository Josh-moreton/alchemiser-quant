# Codebase Metrics Report

Generated on: Tue Sep 16 17:27:41 UTC 2025

## Executive Summary

- **Total Files**: 202
- **Total Lines of Code**: 22,076
- **Total Import Statements**: 1,033
- **Unused Imports Found**: 0

## 1. File Count Analysis

### By File Type
- **.py**: 181 files
- **.md**: 6 files
- **(no extension)**: 3 files
- **.json**: 3 files
- **.toml**: 2 files
- **.yaml**: 2 files
- **.code-workspace**: 1 files
- **.lock**: 1 files
- **.png**: 1 files
- **.sh**: 1 files
- **.txt**: 1 files


### By Category
- **Source Code**: 181 files
- **Test Files**: 0 files  
- **Configuration**: 7 files
- **Documentation**: 7 files
- **Other**: 7 files

### Code-to-Test Ratio
Test Coverage Ratio: 0.00
*(Lower values indicate potential testing gaps)*

## 2. Line Count Analysis

### Overall Statistics
- **Total Lines**: 32,607
- **Code Lines**: 22,076 (67.7%)
- **Comment Lines**: 4,021 (12.3%)
- **Blank Lines**: 6,510 (20.0%)

### By Module/Package
- **the_alchemiser.shared**: 20,232 lines (118 files, 13,581 code lines)
- **the_alchemiser.strategy_v2**: 6,030 lines (34 files, 4,102 code lines)
- **the_alchemiser.orchestration**: 2,722 lines (6 files, 1,893 code lines)
- **the_alchemiser.execution_v2**: 1,717 lines (10 files, 1,199 code lines)
- **the_alchemiser.portfolio_v2**: 941 lines (9 files, 619 code lines)
- **the_alchemiser**: 789 lines (3 files, 551 code lines)


### Largest Files (Top 10)
- **the_alchemiser/shared/cli/cli_formatter.py**: 1,455 lines
- **the_alchemiser/shared/brokers/alpaca_manager.py**: 1,310 lines
- **the_alchemiser/shared/errors/error_handler.py**: 1,167 lines
- **the_alchemiser/shared/services/real_time_pricing.py**: 1,112 lines
- **the_alchemiser/orchestration/trading_orchestrator.py**: 788 lines
- **the_alchemiser/strategy_v2/engines/klm/engine.py**: 769 lines
- **the_alchemiser/shared/math/trading_math.py**: 752 lines
- **the_alchemiser/shared/notifications/templates/portfolio.py**: 721 lines
- **the_alchemiser/execution_v2/core/smart_execution_strategy.py**: 698 lines
- **the_alchemiser/strategy_v2/engines/tecl/engine.py**: 672 lines


### Complexity Hotspots (>100 code lines)
- **the_alchemiser/shared/cli/cli_formatter.py**: 1,030 code lines
- **the_alchemiser/shared/brokers/alpaca_manager.py**: 957 code lines
- **the_alchemiser/shared/errors/error_handler.py**: 832 code lines
- **the_alchemiser/shared/services/real_time_pricing.py**: 727 code lines
- **the_alchemiser/orchestration/trading_orchestrator.py**: 587 code lines
- **the_alchemiser/strategy_v2/engines/klm/engine.py**: 573 code lines
- **the_alchemiser/shared/notifications/templates/portfolio.py**: 572 code lines
- **the_alchemiser/shared/math/trading_math.py**: 557 code lines
- **the_alchemiser/execution_v2/core/smart_execution_strategy.py**: 490 code lines
- **the_alchemiser/strategy_v2/engines/tecl/engine.py**: 476 code lines
- **the_alchemiser/strategy_v2/engines/nuclear/engine.py**: 475 code lines
- **the_alchemiser/shared/logging/logging_utils.py**: 447 code lines
- **the_alchemiser/strategy_v2/engines/klm/variants/variant_530_18.py**: 435 code lines
- **the_alchemiser/orchestration/portfolio_orchestrator.py**: 386 code lines
- **the_alchemiser/orchestration/strategy_orchestrator.py**: 361 code lines


## 3. Import and Dependency Analysis

### Import Statistics
- **Total Import Statements**: 1,033
- **Unique Imports**: 230
- **Internal Imports**: 87
- **External Dependencies**: 143

### Internal Module Dependencies
- **scripts.probe_realtime_pricing** imports: the_alchemiser.shared.services.real_time_pricing, the_alchemiser.shared.types.market_data
- **the_alchemiser.execution_v2** imports: the_alchemiser.execution_v2.models.execution_result, the_alchemiser.execution_v2.core.execution_manager
- **the_alchemiser.execution_v2.core** imports: the_alchemiser.execution_v2.core.executor, the_alchemiser.execution_v2.core.execution_tracker, the_alchemiser.execution_v2.core.execution_manager
- **the_alchemiser.execution_v2.core.execution_manager** imports: the_alchemiser.shared.dto.rebalance_plan_dto, the_alchemiser.shared.brokers.alpaca_manager, the_alchemiser.execution_v2.models.execution_result, the_alchemiser.execution_v2.core.smart_execution_strategy, the_alchemiser.execution_v2.core.executor
- **the_alchemiser.execution_v2.core.execution_tracker** imports: the_alchemiser.execution_v2.models.execution_result, the_alchemiser.shared.dto.rebalance_plan_dto
- **the_alchemiser.execution_v2.core.executor** imports: the_alchemiser.shared.dto.rebalance_plan_dto, the_alchemiser.shared.dto.execution_dto, the_alchemiser.shared.brokers.alpaca_manager, the_alchemiser.execution_v2.models.execution_result, the_alchemiser.shared.services.real_time_pricing, the_alchemiser.execution_v2.core.smart_execution_strategy
- **the_alchemiser.execution_v2.core.smart_execution_strategy** imports: the_alchemiser.shared.brokers.alpaca_manager, the_alchemiser.execution_v2.utils.liquidity_analysis, the_alchemiser.shared.services.real_time_pricing, the_alchemiser.shared.types.market_data
- **the_alchemiser.execution_v2.models** imports: the_alchemiser.execution_v2.models.execution_result
- **the_alchemiser.execution_v2.utils.liquidity_analysis** imports: the_alchemiser.shared.types.market_data
- **the_alchemiser.lambda_handler** imports: the_alchemiser.shared.config.secrets_adapter, the_alchemiser.shared.dto, the_alchemiser.shared.logging.logging_utils, the_alchemiser.shared.config.config, the_alchemiser.shared.types.exceptions, the_alchemiser.main, the_alchemiser.shared.errors.error_handler
- **the_alchemiser.main** imports: the_alchemiser.shared.config.secrets_adapter, the_alchemiser.shared.logging.logging_utils, the_alchemiser.shared.config.config, the_alchemiser.shared.types.exceptions, the_alchemiser.shared.events, the_alchemiser.orchestration.event_driven_orchestrator, the_alchemiser.shared.errors.error_handler, the_alchemiser.shared.utils.service_factory, the_alchemiser.shared.cli.trading_executor, the_alchemiser.shared.config.container, the_alchemiser.shared.cli.cli_formatter
- **the_alchemiser.orchestration.event_driven_orchestrator** imports: the_alchemiser.shared.events, the_alchemiser.shared.logging.logging_utils, the_alchemiser.shared.config.container
- **the_alchemiser.orchestration.portfolio_orchestrator** imports: the_alchemiser.shared.logging.logging_utils, the_alchemiser.shared.config.config, the_alchemiser.shared.dto.consolidated_portfolio_dto, the_alchemiser.shared.events, the_alchemiser.shared.dto.rebalance_plan_dto, the_alchemiser.shared.schemas.common, the_alchemiser.portfolio_v2, the_alchemiser.shared.dto.strategy_allocation_dto, the_alchemiser.shared.utils.portfolio_calculations, the_alchemiser.shared.dto.portfolio_state_dto, the_alchemiser.shared.config.container
- **the_alchemiser.orchestration.signal_orchestrator** imports: the_alchemiser.shared.logging.logging_utils, the_alchemiser.orchestration.strategy_orchestrator, the_alchemiser.shared.config.config, the_alchemiser.shared.types.exceptions, the_alchemiser.shared.dto.consolidated_portfolio_dto, the_alchemiser.shared.events, the_alchemiser.shared.types.strategy_types, the_alchemiser.strategy_v2.engines.nuclear, the_alchemiser.shared.utils.strategy_utils, the_alchemiser.shared.value_objects.symbol, the_alchemiser.shared.types, the_alchemiser.shared.config.container, the_alchemiser.shared.dto.signal_dto
- **the_alchemiser.orchestration.strategy_orchestrator** imports: the_alchemiser.shared.value_objects.symbol, the_alchemiser.strategy_v2.engines.tecl.engine, the_alchemiser.shared.types.exceptions, the_alchemiser.shared.types.strategy_registry, the_alchemiser.shared.types.strategy_types, the_alchemiser.strategy_v2.engines.nuclear.engine, the_alchemiser.shared.config.confidence_config, the_alchemiser.strategy_v2.engines.klm.engine, the_alchemiser.shared.types.market_data_port, the_alchemiser.shared.types
- **the_alchemiser.orchestration.trading_orchestrator** imports: the_alchemiser.shared.logging.logging_utils, the_alchemiser.shared.config.config, the_alchemiser.shared.types.exceptions, the_alchemiser.shared.events, the_alchemiser.shared.dto.rebalance_plan_dto, the_alchemiser.shared.schemas.common, the_alchemiser.shared.notifications.email_utils, the_alchemiser.orchestration.portfolio_orchestrator, the_alchemiser.execution_v2.models.execution_result, the_alchemiser.shared.dto.portfolio_state_dto, the_alchemiser.shared.errors.error_handler, the_alchemiser.orchestration.signal_orchestrator, the_alchemiser.shared.config.container
- **the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter** imports: the_alchemiser.shared.brokers.alpaca_manager, the_alchemiser.shared.logging.logging_utils
- **the_alchemiser.portfolio_v2.core.planner** imports: the_alchemiser.shared.types.exceptions, the_alchemiser.shared.dto.rebalance_plan_dto, the_alchemiser.shared.dto.strategy_allocation_dto, the_alchemiser.shared.logging.logging_utils
- **the_alchemiser.portfolio_v2.core.portfolio_service** imports: the_alchemiser.shared.logging.logging_utils, the_alchemiser.shared.types.exceptions, the_alchemiser.shared.dto.rebalance_plan_dto, the_alchemiser.shared.dto.strategy_allocation_dto, the_alchemiser.shared.brokers.alpaca_manager
- **the_alchemiser.portfolio_v2.core.state_reader** imports: the_alchemiser.shared.logging.logging_utils, the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter
- **the_alchemiser.shared.brokers.alpaca_manager** imports: the_alchemiser.shared.protocols.repository, the_alchemiser.shared.utils.price_discovery_utils, the_alchemiser.shared.dto.execution_report_dto, the_alchemiser.shared.dto.broker_dto
- **the_alchemiser.shared.cli.base_cli** imports: the_alchemiser.shared.cli.strategy_tracking_utils, the_alchemiser.shared.logging.logging_utils, the_alchemiser.shared.config.config, the_alchemiser.shared.schemas.common, the_alchemiser.shared.config.container, the_alchemiser.shared.cli.cli_formatter
- **the_alchemiser.shared.cli.cli** imports: the_alchemiser.shared.config.secrets_adapter, the_alchemiser.shared.cli.strategy_tracking_utils, the_alchemiser.shared.logging.logging_utils, the_alchemiser.shared.types.exceptions, the_alchemiser.shared.config.secrets_manager, the_alchemiser.main, the_alchemiser.shared.brokers.alpaca_manager, the_alchemiser.shared.errors.error_handler, the_alchemiser.shared.cli.cli_formatter
- **the_alchemiser.shared.cli.cli_formatter** imports: the_alchemiser.shared.math.num, the_alchemiser.strategy_v2.engines.nuclear, the_alchemiser.shared.schemas.common, the_alchemiser.shared.value_objects.core_types
- **the_alchemiser.shared.cli.dashboard_utils** imports: the_alchemiser.shared.value_objects.core_types
- **the_alchemiser.shared.cli.strategy_tracking_utils** imports: the_alchemiser.shared.logging.logging_utils, the_alchemiser.shared.protocols.strategy_tracking
- **the_alchemiser.shared.cli.trading_executor** imports: the_alchemiser.shared.cli.strategy_tracking_utils, the_alchemiser.shared.config.config, the_alchemiser.shared.protocols.strategy_tracking, the_alchemiser.orchestration.trading_orchestrator, the_alchemiser.shared.cli.base_cli, the_alchemiser.shared.config.container, the_alchemiser.shared.cli.cli_formatter
- **the_alchemiser.shared.config.config_providers** imports: the_alchemiser.shared.config.secrets_adapter, the_alchemiser.shared.config.config
- **the_alchemiser.shared.config.config_service** imports: the_alchemiser.shared.config.config
- **the_alchemiser.shared.config.container** imports: the_alchemiser.shared.config.infrastructure_providers, the_alchemiser.shared.config.service_providers, the_alchemiser.shared.config.config_providers
- **the_alchemiser.shared.config.infrastructure_providers** imports: the_alchemiser.shared.brokers, the_alchemiser.shared.services.market_data_service
- **the_alchemiser.shared.config.secrets_adapter** imports: the_alchemiser.shared.config, the_alchemiser.shared.config.config
- **the_alchemiser.shared.config.secrets_manager** imports: the_alchemiser.shared.config.secrets_adapter
- **the_alchemiser.shared.config.service_providers** imports: the_alchemiser.shared.events.bus, the_alchemiser.execution_v2.core.execution_manager
- **the_alchemiser.shared.dto** imports: the_alchemiser.shared.dto.rebalance_plan_dto, the_alchemiser.shared.dto.lambda_event_dto, the_alchemiser.shared.dto.strategy_allocation_dto, the_alchemiser.shared.dto.portfolio_state_dto, the_alchemiser.shared.dto.execution_report_dto, the_alchemiser.shared.dto.order_request_dto, the_alchemiser.shared.dto.signal_dto
- **the_alchemiser.shared.dto.broker_dto** imports: the_alchemiser.shared.schemas.base
- **the_alchemiser.shared.errors.error_handler** imports: the_alchemiser.shared.notifications.client, the_alchemiser.shared.logging.logging_utils, the_alchemiser.shared.value_objects.identifier, the_alchemiser.shared.types.exceptions, the_alchemiser.shared.types.trading_errors, the_alchemiser.shared.notifications.templates
- **the_alchemiser.shared.mappers.execution_summary_mapping** imports: the_alchemiser.shared.dto.portfolio_state_dto, the_alchemiser.shared.schemas.execution_summary
- **the_alchemiser.shared.mappers.market_data_mappers** imports: the_alchemiser.shared.types.market_data, the_alchemiser.shared.types.quote
- **the_alchemiser.shared.math.asset_info** imports: the_alchemiser.shared.value_objects.symbol, the_alchemiser.shared.protocols.asset_metadata
- **the_alchemiser.shared.math.math_utils** imports: the_alchemiser.shared.math.num
- **the_alchemiser.shared.math.trading_math** imports: the_alchemiser.shared.services.tick_size_service
- **the_alchemiser.shared.notifications.client** imports: the_alchemiser.shared.schemas.reporting
- **the_alchemiser.shared.notifications.config** imports: the_alchemiser.shared.config.secrets_adapter, the_alchemiser.shared.schemas.reporting, the_alchemiser.shared.config.config
- **the_alchemiser.shared.notifications.templates.email_facade** imports: the_alchemiser.shared.value_objects.core_types
- **the_alchemiser.shared.notifications.templates.multi_strategy** imports: the_alchemiser.shared.schemas.common
- **the_alchemiser.shared.notifications.templates.portfolio** imports: the_alchemiser.execution_v2.models.execution_result, the_alchemiser.shared.schemas.common, the_alchemiser.shared.value_objects.core_types
- **the_alchemiser.shared.persistence.factory** imports: the_alchemiser.shared.persistence.local_handler, the_alchemiser.shared.persistence.s3_handler, the_alchemiser.shared.protocols.persistence
- **the_alchemiser.shared.protocols.asset_metadata** imports: the_alchemiser.shared.value_objects.symbol
- **the_alchemiser.shared.protocols.repository** imports: the_alchemiser.shared.dto.execution_report_dto
- **the_alchemiser.shared.schemas.accounts** imports: the_alchemiser.shared.schemas.base
- **the_alchemiser.shared.schemas.cli** imports: the_alchemiser.shared.value_objects.core_types
- **the_alchemiser.shared.schemas.common** imports: the_alchemiser.shared.dto.portfolio_state_dto, the_alchemiser.shared.schemas.execution_summary, the_alchemiser.shared.value_objects.core_types
- **the_alchemiser.shared.schemas.enriched_data** imports: the_alchemiser.shared.schemas.base
- **the_alchemiser.shared.schemas.execution_summary** imports: the_alchemiser.shared.value_objects.core_types
- **the_alchemiser.shared.schemas.market_data** imports: the_alchemiser.shared.schemas.base
- **the_alchemiser.shared.schemas.operations** imports: the_alchemiser.shared.schemas.base
- **the_alchemiser.shared.schemas.reporting** imports: the_alchemiser.shared.value_objects.core_types
- **the_alchemiser.shared.services.market_data_service** imports: the_alchemiser.shared.logging.logging_utils, the_alchemiser.shared.types.quote, the_alchemiser.shared.types.exceptions, the_alchemiser.shared.types.market_data_port, the_alchemiser.shared.types.market_data, the_alchemiser.shared.brokers.alpaca_manager, the_alchemiser.shared.value_objects.symbol
- **the_alchemiser.shared.services.real_time_pricing** imports: the_alchemiser.shared.brokers.alpaca_utils, the_alchemiser.shared.utils.price_discovery_utils, the_alchemiser.shared.types.market_data
- **the_alchemiser.shared.types.account** imports: the_alchemiser.shared.value_objects.core_types
- **the_alchemiser.shared.types.market_data** imports: the_alchemiser.shared.value_objects.core_types
- **the_alchemiser.shared.types.market_data_port** imports: the_alchemiser.shared.value_objects.symbol, the_alchemiser.shared.types.market_data, the_alchemiser.shared.types.quote
- **the_alchemiser.shared.types.percentage** imports: the_alchemiser.shared.utils.validation_utils
- **the_alchemiser.shared.types.quantity** imports: the_alchemiser.shared.utils.validation_utils
- **the_alchemiser.shared.types.strategy_registry** imports: the_alchemiser.shared.types.strategy_types
- **the_alchemiser.shared.types.strategy_value_objects** imports: the_alchemiser.shared.value_objects.symbol, the_alchemiser.shared.types.percentage
- **the_alchemiser.shared.types.trading_errors** imports: the_alchemiser.shared.types.exceptions
- **the_alchemiser.shared.utils.decorators** imports: the_alchemiser.shared.types.exceptions
- **the_alchemiser.shared.utils.error_reporter** imports: the_alchemiser.shared.types.exceptions
- **the_alchemiser.shared.utils.service_factory** imports: the_alchemiser.shared.config.container, the_alchemiser.execution_v2.core.execution_manager
- **the_alchemiser.shared.utils.strategy_utils** imports: the_alchemiser.shared.types.strategy_types, the_alchemiser.shared.config.config
- **the_alchemiser.strategy_v2.engines.klm.base_variant** imports: the_alchemiser.shared.utils.common, the_alchemiser.shared.value_objects.core_types
- **the_alchemiser.strategy_v2.engines.klm.engine** imports: the_alchemiser.shared.value_objects.symbol, the_alchemiser.shared.math.math_utils, the_alchemiser.shared.types.exceptions, the_alchemiser.shared.types.percentage, the_alchemiser.strategy_v2.indicators.indicator_utils, the_alchemiser.shared.types.market_data, the_alchemiser.shared.config.confidence_config, the_alchemiser.strategy_v2.indicators.indicators, the_alchemiser.shared.value_objects.core_types, the_alchemiser.shared.utils.common, the_alchemiser.shared.types.market_data_port, the_alchemiser.shared.types
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_1200_28** imports: the_alchemiser.shared.utils.common, the_alchemiser.shared.value_objects.core_types
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_1280_26** imports: the_alchemiser.shared.utils.common, the_alchemiser.shared.value_objects.core_types
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_410_38** imports: the_alchemiser.shared.utils.common, the_alchemiser.shared.value_objects.core_types
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_506_38** imports: the_alchemiser.shared.utils.common, the_alchemiser.shared.value_objects.core_types
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_520_22** imports: the_alchemiser.shared.utils.common, the_alchemiser.shared.value_objects.core_types
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_530_18** imports: the_alchemiser.shared.utils.common, the_alchemiser.shared.value_objects.core_types
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_830_21** imports: the_alchemiser.shared.utils.common, the_alchemiser.shared.value_objects.core_types
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_nova** imports: the_alchemiser.shared.utils.common, the_alchemiser.shared.value_objects.core_types
- **the_alchemiser.strategy_v2.engines.nuclear.engine** imports: the_alchemiser.shared.value_objects.symbol, the_alchemiser.shared.logging.logging_utils, the_alchemiser.shared.types.exceptions, the_alchemiser.shared.types.percentage, the_alchemiser.strategy_v2.indicators.indicator_utils, the_alchemiser.shared.types.market_data, the_alchemiser.shared.config.confidence_config, the_alchemiser.strategy_v2.indicators.indicators, the_alchemiser.shared.types.market_data_port, the_alchemiser.shared.types
- **the_alchemiser.strategy_v2.engines.tecl.engine** imports: the_alchemiser.shared.value_objects.symbol, the_alchemiser.shared.logging.logging_utils, the_alchemiser.shared.types.percentage, the_alchemiser.strategy_v2.indicators.indicator_utils, the_alchemiser.shared.types.market_data, the_alchemiser.shared.config.confidence_config, the_alchemiser.strategy_v2.indicators.indicators, the_alchemiser.shared.utils.common, the_alchemiser.shared.types.market_data_port, the_alchemiser.shared.types


### External Dependencies (Most Common)
- **alpaca**: 11 import(s)
- **rich**: 7 import(s)
- **templates**: 5 import(s)
- **email**: 4 import(s)
- **core**: 4 import(s)
- **dto**: 3 import(s)
- **logging**: 3 import(s)
- **shared**: 3 import(s)
- **utils**: 2 import(s)
- **collections**: 2 import(s)
- **models**: 2 import(s)
- **adapters**: 2 import(s)
- **market_data**: 1 import(s)
- **variant_830_21**: 1 import(s)
- **signal_orchestrator**: 1 import(s)


### Circular Dependencies
✅ No circular dependencies detected


### Unreachable Modules
- **scripts.probe_realtime_pricing** (never imported)
- **the_alchemiser** (never imported)
- **the_alchemiser.execution_v2** (never imported)
- **the_alchemiser.execution_v2.core** (never imported)
- **the_alchemiser.execution_v2.models** (never imported)
- **the_alchemiser.execution_v2.utils** (never imported)
- **the_alchemiser.lambda_handler** (never imported)
- **the_alchemiser.orchestration** (never imported)
- **the_alchemiser.portfolio_v2.adapters** (never imported)
- **the_alchemiser.portfolio_v2.core** (never imported)
- **the_alchemiser.portfolio_v2.core.planner** (never imported)
- **the_alchemiser.portfolio_v2.core.portfolio_service** (never imported)
- **the_alchemiser.portfolio_v2.core.state_reader** (never imported)
- **the_alchemiser.portfolio_v2.models** (never imported)
- **the_alchemiser.portfolio_v2.models.portfolio_snapshot** (never imported)
- **the_alchemiser.shared** (never imported)
- **the_alchemiser.shared.cli.cli** (never imported)
- **the_alchemiser.shared.cli.dashboard_utils** (never imported)
- **the_alchemiser.shared.config.config_service** (never imported)
- **the_alchemiser.shared.config.env_loader** (never imported)
- **the_alchemiser.shared.errors** (never imported)
- **the_alchemiser.shared.errors.context** (never imported)
- **the_alchemiser.shared.events.base** (never imported)
- **the_alchemiser.shared.events.handlers** (never imported)
- **the_alchemiser.shared.events.schemas** (never imported)
- **the_alchemiser.shared.logging** (never imported)
- **the_alchemiser.shared.mappers.execution_summary_mapping** (never imported)
- **the_alchemiser.shared.mappers.market_data_mappers** (never imported)
- **the_alchemiser.shared.math** (never imported)
- **the_alchemiser.shared.math.asset_info** (never imported)
- **the_alchemiser.shared.math.trading_math** (never imported)
- **the_alchemiser.shared.notifications.config** (never imported)
- **the_alchemiser.shared.notifications.templates.base** (never imported)
- **the_alchemiser.shared.notifications.templates.email_facade** (never imported)
- **the_alchemiser.shared.notifications.templates.multi_strategy** (never imported)
- **the_alchemiser.shared.notifications.templates.performance** (never imported)
- **the_alchemiser.shared.notifications.templates.portfolio** (never imported)
- **the_alchemiser.shared.notifications.templates.signals** (never imported)
- **the_alchemiser.shared.persistence** (never imported)
- **the_alchemiser.shared.persistence.factory** (never imported)
- **the_alchemiser.shared.protocols.alpaca** (never imported)
- **the_alchemiser.shared.protocols.order_like** (never imported)
- **the_alchemiser.shared.schemas** (never imported)
- **the_alchemiser.shared.schemas.accounts** (never imported)
- **the_alchemiser.shared.schemas.cli** (never imported)
- **the_alchemiser.shared.schemas.enriched_data** (never imported)
- **the_alchemiser.shared.schemas.errors** (never imported)
- **the_alchemiser.shared.schemas.market_data** (never imported)
- **the_alchemiser.shared.schemas.operations** (never imported)
- **the_alchemiser.shared.services** (never imported)
- **the_alchemiser.shared.types.account** (never imported)
- **the_alchemiser.shared.types.broker_enums** (never imported)
- **the_alchemiser.shared.types.money** (never imported)
- **the_alchemiser.shared.types.quantity** (never imported)
- **the_alchemiser.shared.types.strategy_protocol** (never imported)
- **the_alchemiser.shared.types.strategy_value_objects** (never imported)
- **the_alchemiser.shared.types.time_in_force** (never imported)
- **the_alchemiser.shared.utils** (never imported)
- **the_alchemiser.shared.utils.config** (never imported)
- **the_alchemiser.shared.utils.context** (never imported)
- **the_alchemiser.shared.utils.decorators** (never imported)
- **the_alchemiser.shared.utils.dto_conversion** (never imported)
- **the_alchemiser.shared.utils.error_reporter** (never imported)
- **the_alchemiser.shared.utils.serialization** (never imported)
- **the_alchemiser.shared.utils.timezone_utils** (never imported)
- **the_alchemiser.shared.value_objects** (never imported)
- **the_alchemiser.strategy_v2** (never imported)
- **the_alchemiser.strategy_v2.adapters** (never imported)
- **the_alchemiser.strategy_v2.adapters.feature_pipeline** (never imported)
- **the_alchemiser.strategy_v2.adapters.market_data_adapter** (never imported)
- **the_alchemiser.strategy_v2.cli** (never imported)
- **the_alchemiser.strategy_v2.core** (never imported)
- **the_alchemiser.strategy_v2.core.factory** (never imported)
- **the_alchemiser.strategy_v2.core.orchestrator** (never imported)
- **the_alchemiser.strategy_v2.core.registry** (never imported)
- **the_alchemiser.strategy_v2.engines** (never imported)
- **the_alchemiser.strategy_v2.engines.klm** (never imported)
- **the_alchemiser.strategy_v2.engines.klm.base_variant** (never imported)
- **the_alchemiser.strategy_v2.engines.klm.variants** (never imported)
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_1200_28** (never imported)
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_1280_26** (never imported)
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_410_38** (never imported)
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_506_38** (never imported)
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_520_22** (never imported)
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_530_18** (never imported)
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_830_21** (never imported)
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_nova** (never imported)
- **the_alchemiser.strategy_v2.engines.nuclear.constants** (never imported)
- **the_alchemiser.strategy_v2.engines.nuclear.logic** (never imported)
- **the_alchemiser.strategy_v2.engines.tecl** (never imported)
- **the_alchemiser.strategy_v2.errors** (never imported)
- **the_alchemiser.strategy_v2.indicators** (never imported)
- **the_alchemiser.strategy_v2.models** (never imported)
- **the_alchemiser.strategy_v2.models.context** (never imported)


## 4. Import Issues (Ruff Analysis)

### Unused Imports
✅ No unused imports detected


## 5. Recommendations

### File Organization
- **181 source files** vs **0 test files**
  - ⚠️ **Low test coverage ratio** - consider adding more test files

### Complexity Management
- **69 files** have >100 code lines
  - Consider refactoring largest files for maintainability

### Import Cleanup
- ✅ No unused imports detected
- ✅ No circular dependencies to resolve


---

## Reproducibility

This report was generated using:

```bash
# Install dependencies
poetry install

# Run analysis
python /tmp/codebase_analyzer.py /home/runner/work/alchemiser-quant/alchemiser-quant

# For import analysis
poetry run ruff check the_alchemiser --select F401

# For dependency validation  
poetry run import-linter
```

**Tools Used**: Python AST parsing, ruff, poetry, custom analysis scripts
**Analysis Date**: 2025-09-16
