# Module File Count Report

**Generated**: September 2025 (Updated)  
**Repository**: alchemiser-quant  
**Total Modules Analyzed**: 4

## Executive Summary

This report provides a comprehensive overview of all Python files within the four core modules of `the_alchemiser`: **strategy**, **portfolio**, **execution**, and **shared**. Each module follows the modular architecture with clear separation of concerns and well-defined responsibilities.

### Module Overview

| Module | File Count | Primary Responsibility |
|--------|------------|----------------------|
| **strategy** | 68 files | Signal generation, indicator calculation, ML models, regime detection |
| **portfolio** | 53 files | Portfolio state management, sizing, rebalancing logic, risk management |
| **execution** | 68 files | Broker API integrations, order placement, smart execution, error handling |
| **shared** | 91 files | DTOs, utilities, logging, cross-cutting concerns, common value objects |
| **Root level** | 3 files | Main entry points and module initialization |
| **Total** | **283 files** | Complete trading system implementation |

---

## Strategy Module (68 files)

**Business Unit**: strategy  
**Status**: current  
**Purpose**: Signal generation and indicator calculation for trading strategies

### Directory Structure

#### Root Level
- `__init__.py` - Main module initialization and exports



#### data/ (10 files)
Market data services and utilities:
- `__init__.py` - Data services module exports
- `domain_mapping.py` - Domain object mapping utilities
- `market_data_client.py` - Market data client implementation
- `market_data_service.py` - Enhanced market data operations with caching
- `price_fetching_utils.py` - Price fetching utility functions
- `price_service.py` - Price data service implementation
- `price_utils.py` - Price calculation utilities  
- `shared_market_data_service.py` - Shared market data service
- `strategy_market_data_service.py` - Strategy-specific market data service
- `streaming_service.py` - Real-time market data streaming

#### dsl/ (9 files)
Domain Specific Language for strategy evaluation:
- `__init__.py` - DSL module initialization
- `ast.py` - Abstract Syntax Tree node definitions
- `errors.py` - DSL-specific error handling
- `evaluator.py` - DSL expression evaluator
- `evaluator_cache.py` - Caching for DSL evaluations
- `interning.py` - String interning utilities for performance
- `optimization_config.py` - DSL optimization configuration
- `parser.py` - DSL parser implementation
- `strategy_loader.py` - Strategy file loader and validator

#### engines/ (29 files)
Strategy implementations and execution engines:

**Core (2 files)**:
- `__init__.py` - Core engine exports
- `trading_engine.py` - Base trading engine implementation

**Main Engines (7 files)**:
- `__init__.py` - Engine module exports
- `engine.py` - Base strategy engine
- `nuclear_logic.py` - Nuclear strategy logic implementation  
- `nuclear_typed_engine.py` - Typed nuclear strategy engine
- `strategy_manager.py` - Strategy management and orchestration
- `tecl_strategy_engine.py` - TECL strategy engine implementation
- `typed_klm_ensemble_engine.py` - Typed KLM ensemble engine

**Entities (1 file)**:
- `entities/__init__.py` - Strategy entity exports

**KLM Workers (10 files)**:
- `klm_workers/__init__.py` - KLM workers module exports
- `klm_workers/base_klm_variant.py` - Base class for KLM variants
- `klm_workers/variant_1200_28.py` - KLM variant 1200/28
- `klm_workers/variant_1280_26.py` - KLM variant 1280/26
- `klm_workers/variant_410_38.py` - KLM variant 410/38
- `klm_workers/variant_506_38.py` - KLM variant 506/38
- `klm_workers/variant_520_22.py` - KLM variant 520/22
- `klm_workers/variant_530_18.py` - KLM variant 530/18
- `klm_workers/variant_830_21.py` - KLM variant 830/21
- `klm_workers/variant_nova.py` - KLM Nova variant

**Models (3 files)**:
- `models/__init__.py` - Strategy model exports
- `models/strategy_position_model.py` - Strategy position data model
- `models/strategy_signal_model.py` - Strategy signal data model

**Protocols (2 files)**:
- `protocols/__init__.py` - Strategy protocol exports
- `protocols/strategy_engine.py` - Strategy engine interface definitions

**Value Objects (3 files)**:
- `value_objects/alert.py` - Alert value object
- `value_objects/confidence.py` - Confidence level value object
- `value_objects/strategy_signal.py` - Strategy signal value object

#### errors/ (1 file)
Strategy-specific error handling:
- `strategy_errors.py` - Strategy error definitions and handling

#### indicators/ (3 files)
Technical indicators and market signals:
- `__init__.py` - Indicators module exports
- `indicator_utils.py` - Indicator utility functions
- `indicators.py` - Core technical indicators implementation

#### managers/ (2 files)
Strategy management and orchestration:
- `__init__.py` - Managers module exports
- `typed_strategy_manager.py` - Typed strategy manager implementation

#### mappers/ (4 files)
Data transformation and mapping:
- `__init__.py` - Mapper module exports
- `market_data_adapter.py` - Market data adaptation layer
- `market_data_mapping.py` - Market data mapping utilities
- `strategy_signal_mapping.py` - Strategy signal mapping

#### models/ (1 file)
Strategy data models:
- `__init__.py` - Model exports

#### protocols/ (1 file)
Interface definitions:
- `engine_protocol.py` - Engine protocol definitions

#### registry/ (2 files)
Strategy registration and discovery:
- `__init__.py` - Registry module exports
- `strategy_registry.py` - Strategy registration system

#### schemas/ (2 files)
Strategy data schemas:
- `__init__.py` - Schema module exports
- `strategies.py` - Strategy configuration schemas

#### signals/ (1 file)
Signal processing and generation:
- `__init__.py` - Signals module exports

#### timing/ (1 file)
Market timing utilities:
- `market_timing_utils.py` - Market timing and scheduling utilities

#### types/ (2 files)
Strategy type definitions:
- `__init__.py` - Types module exports
- `strategy.py` - Strategy type definitions

#### validation/ (1 file)
Strategy validation:
- `indicator_validator.py` - Technical indicator validation

---

## Portfolio Module (53 files)

**Business Unit**: portfolio  
**Status**: current  
**Purpose**: Portfolio state management, sizing, rebalancing logic, risk management

### Directory Structure

#### Root Level
- `__init__.py` - Main portfolio module initialization

#### allocation/ (5 files)
Portfolio allocation and rebalancing:
- `rebalance_calculator.py` - Pure rebalancing calculation logic
- `rebalance_execution_service.py` - Rebalance execution orchestration
- `rebalance_plan.py` - Rebalancing plan data structures
- `rebalancing_service.py` - Portfolio rebalancing service
- `rebalancing_service_facade.py` - Rebalancing service facade

#### calculations/ (1 file)
Portfolio mathematical calculations:
- `portfolio_calculations.py` - Core portfolio calculation functions

#### core/ (5 files)
Core portfolio management:
- `__init__.py` - Core module exports
- `portfolio_analysis_service.py` - Portfolio analysis orchestration
- `portfolio_management_facade.py` - Unified portfolio management interface
- `rebalancing_orchestrator.py` - Rebalancing orchestration logic
- `rebalancing_orchestrator_facade.py` - Rebalancing facade interface

#### holdings/ (6 files)
Position and holdings management:
- `position_analyzer.py` - Position analysis utilities
- `position_delta.py` - Position change tracking
- `position_manager.py` - Position management service
- `position_mapping.py` - Position data mapping
- `position_model.py` - Position data model
- `position_service.py` - Position service implementation

#### mappers/ (7 files)
Data transformation and mapping:
- `__init__.py` - Mapper module exports
- `policy_mapping.py` - Policy data mapping
- `portfolio_rebalancing_mapping.py` - Portfolio rebalancing mapping
- `position.py` - Position mapping utilities
- `position_mapping.py` - Position data transformation
- `tracking.py` - Portfolio tracking mapping
- `tracking_mapping.py` - Tracking data mapping
- `tracking_normalization.py` - Tracking data normalization

#### pnl/ (3 files)
Profit and loss tracking:
- `__init__.py` - P&L module exports
- `portfolio_pnl_utils.py` - P&L calculation utilities
- `strategy_order_tracker.py` - Strategy order tracking for P&L

#### policies/ (9 files)
Portfolio policy framework:
- `base_policy.py` - Base policy implementation
- `buying_power_policy.py` - Buying power policy interface
- `buying_power_policy_impl.py` - Buying power policy implementation
- `fractionability_policy.py` - Fractionability policy interface
- `fractionability_policy_impl.py` - Fractionability policy implementation
- `policy_factory.py` - Policy factory for creation
- `position_policy_impl.py` - Position policy implementation
- `rebalancing_policy.py` - Rebalancing policy definitions
- `risk_policy_impl.py` - Risk policy implementation

#### positions/ (1 file)
Position management:
- `position_service.py` - Position service implementation

#### rebalancing/ (1 file)
Rebalancing algorithms and logic:
- `orchestrator.py` - Rebalancing orchestration

#### risk/ (1 file)
Risk management and constraints:
- `__init__.py` - Risk module exports

#### schemas/ (4 files)
Portfolio data schemas:
- `__init__.py` - Schema module exports
- `positions.py` - Position schema definitions
- `rebalancing.py` - Rebalancing schema definitions
- `tracking.py` - Portfolio tracking schemas

#### services/ (1 file)
Portfolio services:
- `__init__.py` - Services module exports

#### state/ (3 files)
Portfolio state management:
- `__init__.py` - State module exports
- `attribution_engine.py` - Attribution state management
- `symbol_classifier.py` - Symbol classification service

#### tracking/ (1 file)
Portfolio tracking integration:
- `integration.py` - Portfolio tracking integration

#### utils/ (2 files)
Portfolio utilities:
- `portfolio_pnl_utils.py` - P&L utility functions
- `valuation_utils.py` - Portfolio valuation utilities

#### valuation/ (1 file)
Portfolio valuation and metrics:
- `__init__.py` - Valuation module exports

---

## Execution Module (68 files)

**Business Unit**: execution  
**Status**: current  
**Purpose**: Broker API integrations, order placement, smart execution, error handling

### Directory Structure

#### Root Level
- `__init__.py` - Main execution module initialization
- `infrastructure.py` - Execution infrastructure setup
- `lifecycle_simplified.py` - Simplified lifecycle management

#### analytics/ (1 file)
Execution analytics:
- `slippage_analyzer.py` - Trade slippage analysis

#### brokers/ (5 files)
Broker API integrations:
- `__init__.py` - Brokers module exports
- `account_service.py` - Broker account service
- `alpaca_client.py` - Alpaca API client implementation
- `alpaca/__init__.py` - Alpaca broker module exports
- `alpaca/adapter.py` - Alpaca broker adapter

#### config/ (1 file)
Execution configuration:
- `execution_config.py` - Execution system configuration

#### core/ (10 files)
Core execution services:
- `__init__.py` - Core module exports
- `account_facade.py` - Account management facade
- `account_management_service.py` - Account management service
- `data_transformation_service.py` - Data transformation service
- `execution_schemas.py` - Execution data schemas
- `executor.py` - Main execution engine
- `lifecycle_coordinator.py` - Lifecycle coordination
- `manager.py` - Core execution manager
- `order_execution_service.py` - Order execution service
- `refactored_execution_manager.py` - Refactored execution manager

#### entities/ (1 file)
Execution entities:
- `order.py` - Order entity and lifecycle management

#### errors/ (4 files)
Error handling and classification:
- `classifier.py` - Error classification system
- `error_categories.py` - Error category definitions
- `error_codes.py` - Execution error codes
- `order_error.py` - Order-specific error handling

#### examples/ (1 file)
Integration examples:
- `canonical_integration.py` - Canonical integration example

#### lifecycle/ (9 files)
Order lifecycle management:
- `__init__.py` - Lifecycle module exports
- `dispatcher.py` - Event dispatcher for order lifecycle
- `events.py` - Lifecycle event definitions
- `exceptions.py` - Lifecycle exception handling
- `manager.py` - Lifecycle management service
- `observers.py` - Lifecycle event observers
- `protocols.py` - Lifecycle interface definitions
- `states.py` - Order state definitions
- `transitions.py` - State transition logic

#### mappers/ (5 files)
Data transformation and mapping:
- `__init__.py` - Mapper module exports
- `broker_integration_mappers.py` - Broker integration mapping
- `core_execution_mappers.py` - Core execution mapping
- `order_domain_mappers.py` - Order domain mapping
- `service_dto_mappers.py` - Service DTO mapping

#### monitoring/ (1 file)
Execution monitoring:
- `websocket_order_monitor.py` - WebSocket order monitoring

#### orders/ (9 files)
Order management and handling:
- `__init__.py` - Orders module exports
- `asset_order_handler.py` - Asset-specific order handling
- `consolidated_validation.py` - Consolidated order validation
- `order.py` - Order entity and data structures
- `order_types.py` - Order type definitions
- `progressive_order_utils.py` - Progressive order utilities
- `request_builder.py` - Generic request builder
- `schemas.py` - Order schema definitions
- `service.py` - Order service implementation

#### pricing/ (3 files)
Smart pricing and execution:
- `__init__.py` - Pricing module exports
- `smart_pricing_handler.py` - Smart pricing logic
- `spread_assessment.py` - Bid-ask spread assessment

#### protocols/ (2 files)
Interface definitions:
- `order_lifecycle.py` - Order lifecycle protocol
- `trading_repository.py` - Trading repository interface

#### schemas/ (2 files)
Execution schemas:
- `alpaca.py` - Alpaca-specific schemas
- `smart_trading.py` - Smart trading schema definitions

#### strategies/ (6 files)
Smart execution strategies:
- `__init__.py` - Strategies module exports
- `aggressive_limit_strategy.py` - Aggressive limit order strategy
- `config.py` - Strategy configuration
- `execution_context_adapter.py` - Execution context adapter
- `repeg_strategy.py` - Re-pegging strategy implementation
- `smart_execution.py` - Smart execution orchestration

#### types/ (1 file)
Execution type definitions:
- `policy_result.py` - Policy result type definitions

---

## Shared Module (91 files)

**Business Unit**: shared  
**Status**: current  
**Purpose**: DTOs, utilities, logging, cross-cutting concerns, common value objects

### Directory Structure

#### Root Level
- `__init__.py` - Main shared module initialization
- `dto_communication_demo.py` - DTO communication demonstration
- `simple_dto_test.py` - Simple DTO testing utilities

#### adapters/ (5 files)
Cross-module integration adapters:
- `__init__.py` - Adapters module exports
- `execution_adapters.py` - Execution module adapters
- `integration_helpers.py` - Integration helper utilities
- `portfolio_adapters.py` - Portfolio module adapters
- `strategy_adapters.py` - Strategy module adapters

#### cli/ (8 files)
Command-line interface utilities:
- `cli.py` - Main CLI interface
- `cli_formatter.py` - CLI output formatting
- `dashboard_utils.py` - Dashboard utility functions
- `error_display_utils.py` - Error display utilities
- `portfolio_calculations.py` - Portfolio calculation CLI utilities
- `signal_analyzer.py` - Signal analysis CLI tools
- `signal_display_utils.py` - Signal display utilities
- `trading_executor.py` - Trading execution CLI

#### config/ (10 files)
Configuration management:
- `__init__.py` - Config module exports
- `bootstrap.py` - Application bootstrap configuration
- `config.py` - Core configuration management
- `config_providers.py` - Configuration providers
- `config_service.py` - Configuration service
- `container.py` - Dependency injection container
- `infrastructure_providers.py` - Infrastructure providers
- `secrets_manager.py` - Secrets management
- `secrets_service.py` - Secrets service
- `service_providers.py` - Service providers

#### dto/ (6 files)
Data transfer objects for inter-module communication:
- `__init__.py` - DTO module exports
- `execution_report_dto.py` - Execution report DTOs
- `order_request_dto.py` - Order request DTOs
- `portfolio_state_dto.py` - Portfolio state DTOs
- `rebalance_plan_dto.py` - Rebalancing plan DTOs
- `signal_dto.py` - Strategy signal DTOs

#### errors/ (3 files)
Error handling and context:
- `__init__.py` - Errors module exports
- `context.py` - Error context management
- `error_handler.py` - Central error handling

#### log/ (1 file)
Legacy logging utilities:
- `__init__.py` - Log module exports

#### logging/ (3 files)
Modern logging infrastructure:
- `__init__.py` - Logging module exports
- `logging.py` - Core logging implementation
- `logging_utils.py` - Logging utility functions

#### mappers/ (3 files)
Data mapping and transformation:
- `execution_summary_mapping.py` - Execution summary mapping
- `market_data_mappers.py` - Market data mapping utilities
- `pandas_time_series.py` - Pandas time series mapping

#### math/ (5 files)
Mathematical utilities and calculations:
- `__init__.py` - Math module exports
- `asset_info.py` - Asset information and fractionability
- `math_utils.py` - General mathematical utilities
- `num.py` - Numeric type utilities
- `trading_math.py` - Trading-specific mathematical functions

#### notifications/ (10 files)
Notification and alerting system:
- `client.py` - Notification client
- `config.py` - Notification configuration
- `email_utils.py` - Email utility functions
- `templates/base.py` - Base notification template
- `templates/error_report.py` - Error report template
- `templates/multi_strategy.py` - Multi-strategy notification template
- `templates/order_confirmation.py` - Order confirmation template
- `templates/portfolio_summary.py` - Portfolio summary template
- `templates/rebalance_notification.py` - Rebalancing notification template
- `templates/signal_alert.py` - Signal alert template

#### protocols/ (6 files)
Interface definitions and protocols:
- `broker_protocol.py` - Broker interface protocol
- `execution_protocol.py` - Execution protocol definitions
- `logger_protocol.py` - Logger interface protocol
- `market_data_protocol.py` - Market data protocol
- `notification_protocol.py` - Notification protocol
- `trading_ports.py` - Trading ports and interfaces

#### reporting/ (1 file)
Reporting utilities:
- `reporting.py` - Report generation utilities

#### schemas/ (11 files)
Data schema definitions:
- `__init__.py` - Schemas module exports
- `accounts.py` - Account schema definitions
- `base.py` - Base schema utilities
- `cli.py` - CLI schema definitions
- `common.py` - Common schema utilities
- `enriched_data.py` - Enriched data schemas
- `errors.py` - Error schema definitions
- `execution_summary.py` - Execution summary schemas
- `market_data.py` - Market data schemas
- `operations.py` - Operations schema definitions
- `reporting.py` - Reporting schema definitions

#### services/ (5 files)
Shared services:
- `__init__.py` - Services module exports
- `alert_service.py` - Alert service implementation
- `real_time_pricing.py` - Real-time pricing service
- `tick_size_service.py` - Tick size service
- `websocket_connection_manager.py` - WebSocket connection management

#### types/ (15 files)
Common value objects and type definitions:
- `__init__.py` - Types module exports
- `account.py` - Account type definitions
- `bar.py` - Market data bar types
- `exceptions.py` - Exception type definitions
- `market_data.py` - Market data types
- `market_data_port.py` - Market data port types
- `money.py` - Money value object
- `order_status.py` - Order status types
- `percentage.py` - Percentage value object
- `quantity.py` - Quantity value object
- `quote.py` - Quote type definitions
- `shared_kernel_types.py` - Shared kernel types
- `strategy_type.py` - Strategy type definitions
- `time_in_force.py` - Time in force types
- `trading_errors.py` - Trading error types

#### utils/ (20 files)
Utility functions and helpers:
- `__init__.py` - Utils module exports
- `account_utils.py` - Account utility functions
- `cache_manager.py` - Cache management utilities
- `common.py` - Common utility functions
- `config.py` - Configuration utilities
- `context.py` - Context management utilities
- `decorators.py` - Utility decorators
- `error_monitoring.py` - Error monitoring utilities
- `error_recovery.py` - Error recovery utilities
- `error_reporter.py` - Error reporting utilities
- `error_scope.py` - Error scope management
- `order_completion_utils.py` - Order completion utilities
- `price_discovery_utils.py` - Price discovery utilities
- `retry_decorator.py` - Retry mechanism decorator
- `s3_utils.py` - AWS S3 utility functions
- `serialization.py` - Data serialization utilities
- `service_factory.py` - Service factory utilities
- `strategy_utils.py` - Strategy utility functions
- `timezone_utils.py` - Timezone handling utilities
- `validation_utils.py` - Validation utility functions

#### value_objects/ (4 files)
Domain value objects:
- `__init__.py` - Value objects module exports
- `core_types.py` - Core value object types
- `identifier.py` - Identifier value objects
- `symbol.py` - Trading symbol value objects

---

## Summary

The four modules represent a comprehensive trading system implementation with clear separation of concerns:

- **Strategy Module (68 files)**: Signal generation system with multiple strategy engines (Nuclear, TECL, KLM), technical indicators, DSL evaluation, and market data services.

- **Portfolio Module (53 files)**: Portfolio management system including position tracking, rebalancing algorithms, risk policies, P&L tracking, and portfolio analytics.

- **Execution Module (68 files)**: Execution system with broker integrations (Alpaca), smart execution strategies, order lifecycle management, and comprehensive error handling.

- **Shared Module (91 files)**: Cross-cutting concerns including DTOs for inter-module communication, common value objects (Money, Symbol), utilities, configuration management, logging infrastructure, and notification systems.

### Architecture Compliance

All modules follow the established architectural principles:
- Clear business unit alignment with proper docstring declarations
- Modular separation with controlled dependencies 
- Comprehensive error handling and logging
- Type safety with full mypy compliance
- Clean interfaces and protocol definitions

**Total System**: 283 Python files implementing a complete quantitative trading platform.