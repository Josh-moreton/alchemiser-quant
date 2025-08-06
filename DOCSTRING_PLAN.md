# Docstring Coverage Plan

This document outlines the steps required to add Google-style docstrings across the project.

## 1. Audit Summary

The following modules, classes, functions, and methods currently lack docstrings and need to be updated. Paths are relative to repository root.

### the_alchemiser package
- `the_alchemiser/__init__.py` – module docstring

### core package
- `the_alchemiser/core/alerts/__init__.py` – module docstring
- `the_alchemiser/core/alerts/alert_service.py`
  - module docstring
  - class `Alert.__init__`
  - method `Alert.to_dict`
  - function `create_alert`
- `the_alchemiser/core/config.py`
  - module docstring
  - classes: `LoggingSettings`, `AlpacaSettings`, `AwsSettings`, `AlertsSettings`, `SecretsManagerSettings`, `StrategySettings`, `EmailSettings`, `DataSettings`, `TrackingSettings`, `ExecutionSettings`
  - method `Settings.settings_customise_sources`
- `the_alchemiser/core/data/__init__.py` – module docstring
- `the_alchemiser/core/data/data_provider.py` – module docstring
- `the_alchemiser/core/error_handler.py`
  - method `ErrorDetails.__init__`
  - method `TradingSystemErrorHandler.__init__`
- `the_alchemiser/core/exceptions.py`
  - constructors for: `OrderExecutionError`, `PositionValidationError`, `StrategyExecutionError`, `IndicatorCalculationError`, `MarketDataError`, `ValidationError`, `S3OperationError`, `RateLimitError`, `LoggingError`, `FileOperationError`, `DatabaseError`, `EnvironmentError`
- `the_alchemiser/core/indicators/__init__.py` – module docstring
- `the_alchemiser/core/logging/__init__.py` – module docstring
- `the_alchemiser/core/logging/logging_utils.py`
  - module docstring
  - method `AlchemiserLoggerAdapter.process`
  - method `StructuredFormatter.format`
- `the_alchemiser/core/secrets/__init__.py` – module docstring

### trading package
- `the_alchemiser/core/trading/__init__.py` – module docstring
- `the_alchemiser/core/trading/klm_ensemble_engine.py`
  - constructor `KLMStrategyEnsemble.__init__`
- `the_alchemiser/core/trading/klm_trading_bot.py`
  - constructor `KLMStrategyEngine.__init__`
  - constructor `KLMTradingBot.__init__`
- `the_alchemiser/core/trading/klm_workers/base_klm_variant.py`
  - constructor `BaseKLMVariant.__init__`
- `the_alchemiser/core/trading/klm_workers/variant_1200_28.py`
  - constructor `KlmVariant120028.__init__`
- `the_alchemiser/core/trading/klm_workers/variant_1280_26.py`
  - constructor `KlmVariant128026.__init__`
- `the_alchemiser/core/trading/klm_workers/variant_410_38.py`
  - constructor `KlmVariant41038.__init__`
- `the_alchemiser/core/trading/klm_workers/variant_506_38.py`
  - constructor `KlmVariant50638.__init__`
- `the_alchemiser/core/trading/klm_workers/variant_520_22.py`
  - constructor `KlmVariant52022.__init__`
- `the_alchemiser/core/trading/klm_workers/variant_530_18.py`
  - constructor `KlmVariant53018.__init__`
- `the_alchemiser/core/trading/klm_workers/variant_830_21.py`
  - constructor `KlmVariant83021.__init__`
- `the_alchemiser/core/trading/klm_workers/variant_nova.py`
  - constructor `KLMVariantNova.__init__`
- `the_alchemiser/core/trading/nuclear_signals.py`
  - classes: `ActionType`, `NuclearStrategyEngine`
  - constructors: `NuclearStrategyEngine.__init__`, `NuclearSignalGenerator.__init__`
- `the_alchemiser/core/trading/strategy_engine.py`
  - constructor `NuclearStrategyEngine.__init__`
  - classes: `BullMarketStrategy`, `BearMarketStrategy`, `OverboughtStrategy`, `SecondaryOverboughtStrategy`, `VoxOverboughtStrategy`
  - methods: `BullMarketStrategy.__init__`, `BullMarketStrategy.recommend`, `BearMarketStrategy.__init__`, `BearMarketStrategy.recommend`, `OverboughtStrategy.recommend`, `SecondaryOverboughtStrategy.recommend`, `VoxOverboughtStrategy.recommend`
- `the_alchemiser/core/trading/strategy_manager.py`
  - constructor `StrategyPosition.__init__`
  - methods: `StrategyPosition.to_dict`, `StrategyPosition.from_dict`
- `the_alchemiser/core/trading/tecl_signals.py`
  - constructors: `TECLStrategyEngine.__init__`, `TECLSignalGenerator.__init__`
- `the_alchemiser/core/trading/tecl_strategy_engine.py`
  - constructor `TECLStrategyEngine.__init__`

### core types
- `the_alchemiser/core/types.py` – add class docstrings for:
  `AccountInfo`, `PositionInfo`, `OrderDetails`, `StrategySignal`, `StrategyPnLSummary`, `StrategyPositionData`, `KLMVariantResult`, `ExecutionResult`, `TradingPlan`, `QuoteData`, `LimitOrderResult`, `WebSocketResult`, `KLMDecision`, `ReportingData`, `DashboardMetrics`, `EmailReportData`, `MarketDataPoint`, `IndicatorData`, `PriceData`, `DataProviderResult`, `BacktestResult`, `PerformanceMetrics`, `TradeAnalysis`, `PortfolioSnapshot`, `ErrorContext`, `CLIOptions`, `CLICommandResult`, `CLISignalData`, `CLIAccountDisplay`, `CLIPortfolioData`, `CLIOrderDisplay`, `ErrorDetailInfo`, `ErrorSummaryData`, `ErrorReportSummary`, `ErrorNotificationData`, `EmailCredentials`, `LambdaEvent`, `OrderHistoryData`, `EmailSummary`

### UI components
- `the_alchemiser/core/ui/__init__.py` – module docstring
- `the_alchemiser/core/ui/cli_formatter.py` – module docstring
- `the_alchemiser/core/ui/email/client.py` – constructor `EmailClient.__init__`
- `the_alchemiser/core/ui/email/config.py` – constructor `EmailConfig.__init__`

### Utilities and validation
- `the_alchemiser/core/utils/__init__.py` – module docstring
- `the_alchemiser/core/utils/s3_utils.py` – constructor `S3FileHandler.__init__`
- `the_alchemiser/core/validation/indicator_validator.py` – constructor `IndicatorValidationSuite.__init__`

### Execution
- `the_alchemiser/execution/__init__.py` – module docstring
- `the_alchemiser/execution/account_service.py`
  - module docstring
  - constructor `AccountService.__init__`
- `the_alchemiser/execution/execution_manager.py`
  - module docstring
  - constructor `ExecutionManager.__init__`
- `the_alchemiser/execution/reporting.py` – module docstring

### Tracking
- `the_alchemiser/tracking/__init__.py` – module docstring
- `the_alchemiser/tracking/integration.py`
  - inner function `wrapper`
  - constructor `StrategyTrackingMixin.__init__`

### Utility modules
- `the_alchemiser/utils/market_timing_utils.py`
  - class `ExecutionStrategy`
  - constructor `MarketOpenTimingEngine.__init__`
- `the_alchemiser/utils/progressive_order_utils.py`
  - method `OrderExecutionParams.__str__`
- `the_alchemiser/utils/spread_assessment.py`
  - classes: `SpreadQuality`, `PreMarketConditions`, `SpreadAnalysis`
  - constructor `SpreadAssessment.__init__`
- `the_alchemiser/utils/websocket_connection_manager.py`
  - method `WebSocketConnectionManager.dummy_handler`
- `the_alchemiser/utils/websocket_order_monitor.py`
  - methods: `OrderCompletionMonitor.on_update`, `OrderCompletionMonitor.dummy_handler`

## 2. Items Not Requiring Docstrings
- All files under `tests/` – these are test modules where docstrings are optional and usually omitted for brevity.
- `scripts/phase16_completion_report.py` and similar reporting scripts contain only top-level print statements and already include module-level summaries; no further docstrings are needed.

## 3. Style Guidelines
- Follow [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
- Format:
  ```python
  def example(arg1: int, arg2: str = "x") -> bool:
      """One-line summary.

      Detailed description if necessary.

      Args:
          arg1: Explanation of arg1.
          arg2: Explanation with default ``"x"``.

      Returns:
          bool: Description of return value.

      Raises:
          ValueError: When arg1 is negative.
      """
  ```
- For functions returning nothing, include `Returns:
    None`.
- Document optional parameters and default values.
- Class docstrings should summarize purpose and list attributes if helpful.
- Property methods should describe computed values.

## 4. Recommended Order of Work
1. **Package and module headers** – add docstrings to all `__init__.py` files and modules without existing documentation.
2. **Core configuration and utilities** – `core/config.py`, logging, alerts, and data modules.
3. **Trading engines and workers** – `core/trading/**`.
4. **Type classes** – `core/types.py`.
5. **Execution and tracking modules**.
6. **Remaining utilities** (`utils/**`).

Working top-down ensures foundational modules are documented before higher-level components that depend on them.

## 5. Programmatic Validation
- Integrate a docstring linter such as `pydocstyle` or `flake8-docstrings` into the project.
- Example command:
  ```bash
  pydocstyle the_alchemiser scripts
  ```
- For full coverage including private helpers, use a custom AST-based script (similar to `missing_docstrings.txt` generation) in CI to fail when any module, class, or function lacks a docstring.

