# The Alchemiser

Internal notes on how the trading bot is put together and how the pieces interact.

## System Architecture

### Configuration and Settings

- `the_alchemiser.core.config` uses Pydantic settings models to load configuration from environment variables and `.env` files.

### Data Layer

- `the_alchemiser.core.data.UnifiedDataProvider` unifies Alpaca REST and WebSocket access to provide account details, quotes and historical data.

### Strategy Layer

- Strategy engines live in `the_alchemiser.core.trading`.
- `MultiStrategyManager` instantiates enabled strategies and keeps per‑strategy position tracking and allocation.

### Execution Layer

- `TradingEngine` orchestrates the full trading cycle: it gathers strategy signals, invokes `PortfolioRebalancer` to compute target allocations and delegates order placement to `SmartExecution`.
- `ExecutionManager` drives multi‑strategy execution; `AccountService` exposes account and position data.

### Error Handling and Monitoring

- **Enhanced Error Handler** (`the_alchemiser.core.error_handler`): Comprehensive error categorization, reporting, and email notification system
- **Error Categories**: CRITICAL, TRADING, DATA, STRATEGY, CONFIGURATION, NOTIFICATION, WARNING
- **Automatic Email Alerts**: Detailed error reports with specific remediation actions sent via email
- **Dead Letter Queue**: Failed Lambda executions captured in SQS for investigation
- **Reduced Retry Policy**: EventBridge scheduler limited to 1 retry to prevent cascade failures
- **Silent Failure Prevention**: All critical operations now raise proper exceptions instead of failing silently

### Tracking and Reporting

- `the_alchemiser.tracking` stores fills, positions and P&L history, while reporting helpers summarise runs for the CLI and email output.

### Command Line Interface

- `the_alchemiser.cli` is built with Typer and provides the `alchemiser` command (`bot`, `trade`, `status`, `deploy`, etc.).

## Execution Flow

1. `load_settings()` builds a typed `Settings` object.
2. `UnifiedDataProvider` connects to Alpaca using those settings.
3. `MultiStrategyManager` runs each strategy and merges their desired portfolios.
4. `TradingEngine` uses `PortfolioRebalancer` to derive required trades.
5. `SmartExecution` submits orders and monitors fills via WebSockets.
6. Results and attribution are persisted by the tracking layer.

## Error Handling Architecture

### Core Error System (`core/error_handler.py`)

The system uses a comprehensive error handling framework designed for autonomous operation:

```python
# Error categorization with automatic email notifications
from the_alchemiser.core.error_handler import TradingSystemErrorHandler

error_handler = TradingSystemErrorHandler()
error_details = error_handler.handle_error(
    error=exception,
    component="ComponentName.method_name", 
    context="operation_description",
    additional_data={"symbol": "AAPL", "qty": 100}
)
```

### Error Categories

- **CRITICAL**: System-level failures that stop all operations
- **TRADING**: Order execution, position validation issues  
- **DATA**: Market data, API connectivity issues
- **STRATEGY**: Strategy calculation, signal generation issues
- **CONFIGURATION**: Config, authentication, setup issues
- **NOTIFICATION**: Email, alert delivery issues
- **WARNING**: Non-critical issues that don't stop execution

### Silent Failure Prevention

All critical trading operations have been audited to prevent silent failures:

1. **Strategy Engine**: Volatility calculations and portfolio allocation now raise `StrategyExecutionError` or `IndicatorCalculationError` instead of returning `None`
2. **Data Provider**: Robust error handling with proper `None`/`[]` returns and logging
3. **Order Execution**: Comprehensive validation and fallback handling
4. **Account Operations**: Detailed error handling with conservative defaults

### Autonomous Operation Features

- **Email Alerts**: Automatic detailed error reports with specific remediation actions
- **Error Context**: Full debugging context captured (component, operation, data, stack trace)
- **Suggested Actions**: Each error type includes specific resolution steps
- **Fail-Fast Design**: EventBridge retry limit reduced to 1 to prevent cascade failures
- **Dead Letter Queue**: Failed executions captured in SQS for investigation

### Error Integration Points

Key components with enhanced error handling:
- `main.py`: Top-level execution error catching and reporting
- `lambda_handler.py`: AWS Lambda-specific error handling with context
- `execution/trading_engine.py`: Trading operation error categorization
- `core/trading/strategy_engine.py`: Strategy calculation error handling
- `core/trading/strategy_manager.py`: Portfolio allocation error management

### Email Notification System

Automatic email alerts include:
- Error categorization and severity
- Component and context information
- Specific remediation actions
- Additional debugging data
- Full stack traces
- Professional HTML formatting

## 2025 Python Practices

- Project managed with Poetry and a single `pyproject.toml`.
- Strict typing checked by `mypy` with `disallow_untyped_defs`.
- Configuration and domain models defined with Pydantic.
- Code style enforced by `black` (line length 100) and linted by `flake8`.
- Tests run with `pytest`; `make test` executes the suite.
- Protocols and dataclasses enable clean dependency injection.
- Rich and Typer keep command‑line interfaces concise and user friendly.

## Development Standards for AI Agents

### Code Quality and Type Safety

**mypy Configuration** (`pyproject.toml`):
```toml
[tool.mypy]
python_version = "3.12"
disallow_untyped_defs = true
disallow_incomplete_defs = true
disallow_untyped_calls = true
warn_return_any = true
warn_unused_ignores = true
```

**Required Practices**:
- ✅ **All functions must have type hints**: Parameters and return types
- ✅ **Use Protocols for dependency injection**: Clean interfaces over inheritance
- ✅ **Pydantic for configuration**: Type-safe settings and data models
- ✅ **Dataclasses for structured data**: Replace dictionaries with typed structures

### Code Formatting and Linting

**Black Configuration**:
- Line length: 100 characters
- Automatic formatting: `make format` or `black .`
- Pre-commit hooks recommended

**Ruff Configuration** (replaces flake8):
```toml
[tool.ruff]
line-length = 100
target-version = "py312"
select = ["E", "W", "F", "I", "N", "UP", "ANN", "S", "BLE", "COM", "C4", "DTZ", "T10", "EM", "EXE", "ISC", "ICN", "G", "INP", "PIE", "T20", "PYI", "PT", "Q", "RSE", "RET", "SLF", "SIM", "TID", "TCH", "ARG", "PTH", "ERA", "PGH", "PL", "TRY", "NPY", "RUF"]
```

**Key Rules for AI Agents**:
- Import sorting with `isort` compatibility
- No unused imports or variables
- Proper exception handling (no bare `except:`)
- Type annotations required
- Security checks enabled

### Project Structure and Organization

```
the_alchemiser/
├── core/                          # Core business logic
│   ├── config.py                  # Pydantic settings models
│   ├── exceptions.py              # Custom exception hierarchy
│   ├── error_handler.py           # Centralized error handling
│   ├── data/                      # Data providers and caching
│   │   └── data_provider.py       # Unified Alpaca API wrapper
│   ├── trading/                   # Strategy engines
│   │   ├── strategy_manager.py    # Multi-strategy coordination
│   │   ├── strategy_engine.py     # Nuclear strategy implementation
│   │   └── tecl_strategy_engine.py # TECL strategy implementation
│   └── ui/                        # User interface components
│       └── email/                 # Email templates and sending
├── execution/                     # Order execution and portfolio management
│   ├── trading_engine.py          # Main trading orchestration
│   ├── smart_execution.py         # Professional order execution
│   ├── alpaca_client.py           # Direct Alpaca API client
│   ├── portfolio_rebalancer.py    # Portfolio rebalancing logic
│   └── account_service.py         # Account and position management
├── tracking/                      # Performance tracking and attribution
│   └── strategy_order_tracker.py  # Per-strategy order tracking
├── utils/                         # Utility functions
│   ├── price_fetching_utils.py    # Price retrieval with fallbacks
│   ├── market_timing_utils.py     # Market hours and timing
│   └── portfolio_pnl_utils.py     # P&L calculation utilities
├── cli.py                         # Typer-based command line interface
├── main.py                        # Main execution entry point
└── lambda_handler.py              # AWS Lambda handler
```

### Dependency Management with Poetry

**Essential Dependencies**:
- `alpaca-py`: Alpaca API client
- `pydantic`: Type-safe configuration and data models
- `rich`: Terminal formatting and progress bars
- `typer`: Command-line interface framework
- `pandas`: Data analysis and manipulation
- `numpy`: Numerical computations
- `boto3`: AWS SDK for Lambda and SQS

**Development Dependencies**:
- `mypy`: Static type checking
- `black`: Code formatting
- `ruff`: Fast Python linter
- `pytest`: Testing framework
- `pytest-cov`: Coverage reporting

### Error Handling Patterns for AI Agents

**Custom Exception Hierarchy** (`core/exceptions.py`):
```python
class AlchemiserError(Exception):
    """Base exception for all Alchemiser errors"""

class TradingClientError(AlchemiserError):
    """Base for trading-related errors"""
    
class StrategyExecutionError(AlchemiserError):
    """Strategy calculation and execution errors"""
    
class IndicatorCalculationError(AlchemiserError):
    """Technical indicator calculation errors"""
```

**Error Handling Pattern**:
```python
from the_alchemiser.core.error_handler import TradingSystemErrorHandler
from the_alchemiser.core.exceptions import StrategyExecutionError

def risky_operation():
    try:
        # Your trading logic here
        pass
    except Exception as e:
        error_handler = TradingSystemErrorHandler()
        error_handler.handle_error(
            error=e,
            component="ComponentName.method_name",
            context="specific_operation_description",
            additional_data={"relevant": "debugging_data"}
        )
        
        # Re-raise if critical, or handle gracefully
        if isinstance(e, StrategyExecutionError):
            raise  # Critical strategy errors should bubble up
        else:
            # Log and continue with fallback
            logging.warning(f"Non-critical error: {e}")
            return safe_fallback_value
```

### Testing Patterns

**Test Structure**:
```python
import pytest
from unittest.mock import Mock, patch
from the_alchemiser.core.trading.strategy_engine import NuclearStrategyEngine

class TestNuclearStrategy:
    def setup_method(self):
        """Setup for each test method"""
        self.engine = NuclearStrategyEngine()
        
    def test_volatility_calculation_with_valid_data(self):
        """Test normal volatility calculation"""
        indicators = {"AAPL": {"price_history": [100, 101, 99, 102]}}
        result = self.engine._get_14_day_volatility("AAPL", indicators)
        assert result > 0
        
    def test_volatility_calculation_raises_on_invalid_data(self):
        """Test that invalid data raises proper exception"""
        with pytest.raises(IndicatorCalculationError):
            self.engine._get_14_day_volatility("INVALID", {})
```

### Configuration Management

**Settings Pattern** (`core/config.py`):
```python
from pydantic import BaseSettings, Field
from typing import Optional

class Settings(BaseSettings):
    """Type-safe configuration with environment variable support"""
    
    alpaca_api_key: str = Field(..., env="ALPACA_API_KEY")
    alpaca_secret_key: str = Field(..., env="ALPACA_SECRET_KEY")
    paper_trading: bool = Field(True, env="PAPER_TRADING")
    email_recipient: str = Field(..., env="EMAIL_RECIPIENT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Usage
def load_settings() -> Settings:
    return Settings()
```

### Protocol-Based Dependency Injection

**Interface Definition**:
```python
from typing import Protocol, Dict, Any

class AccountInfoProvider(Protocol):
    """Protocol for account information providers"""
    def get_account_info(self) -> Dict[str, Any]: ...

class PositionProvider(Protocol):
    """Protocol for position data providers"""
    def get_positions_dict(self) -> Dict[str, Dict[str, Any]]: ...

# Implementation
class TradingEngine:
    def __init__(self, account_provider: AccountInfoProvider):
        self._account_provider = account_provider
        
    def get_account_info(self) -> Dict[str, Any]:
        return self._account_provider.get_account_info()
```

## AWS Infrastructure and Deployment

### EventBridge Scheduler Configuration

The system is designed for autonomous operation with careful retry management:

- **Retry Policy**: Limited to 1 retry attempt (reduced from default 185)
- **Dead Letter Queue**: Failed executions captured in `the-alchemiser-dlq` SQS queue
- **Fail-Fast Design**: Prevents runaway retry loops and excessive Lambda invocations

### Lambda Handler (`lambda_handler.py`)

Enhanced error handling for AWS Lambda execution:

```python
# Automatic error categorization and email notification
def lambda_handler(event, context):
    try:
        result = run_multi_strategy_trading(live_trading=True)
        return {"statusCode": 200, "body": "Success"}
    except Exception as e:
        # Comprehensive error handling with context
        error_handler.handle_error(e, "lambda_execution", "AWS_Lambda")
        raise  # Re-raise for Lambda error handling
```

### Monitoring and Debugging

- **CloudWatch Logs**: Comprehensive logging with error categorization
- **SQS Dead Letter Queue**: 14-day retention for failed execution investigation  
- **Email Alerts**: Immediate notification of critical issues
- **Error Context**: Full debugging information captured automatically

## Quick Commands

```bash
make dev        # install with dev dependencies
make format     # run black
make lint       # run flake8
make test       # run pytest
alchemiser bot  # show current strategy signals
alchemiser trade --live  # live trading
```

## Troubleshooting Guide for AI Agents

### Common Error Patterns and Solutions

1. **StrategyExecutionError in Volatility Calculations**
   - **Location**: `core/trading/strategy_engine.py`
   - **Cause**: Missing volatility data for bear strategy allocation
   - **Solution**: Check data provider connectivity and symbol availability
   - **Fallback**: System uses conservative equal-weight allocation (60/40)

2. **IndicatorCalculationError in Technical Analysis**
   - **Location**: `core/trading/strategy_engine.py._get_14_day_volatility()`
   - **Cause**: Insufficient price history or invalid indicators
   - **Solution**: Verify data availability and indicator calculation logic
   - **Fallback**: Uses RSI-based estimates or fixed volatility values

3. **TradingClientError in Order Execution**
   - **Location**: `execution/alpaca_client.py`
   - **Cause**: API limits, market hours, insufficient funds, position validation
   - **Solution**: Check account status, market hours, and position limits
   - **Fallback**: Order validation prevents invalid orders

4. **MarketDataError in Price Fetching**
   - **Location**: `core/data/data_provider.py`
   - **Cause**: API connectivity, rate limits, symbol unavailability
   - **Solution**: Check API credentials and rate limit status
   - **Fallback**: Historical price fallback and multiple data sources

### Error Handling Flow for AI Agents

When encountering errors in the codebase:

1. **Check Error Category**: Look for error types (CRITICAL, TRADING, DATA, STRATEGY)
2. **Review Context**: Error handler provides component and operation context
3. **Apply Suggested Actions**: Each error includes specific remediation steps
4. **Use Conservative Fallbacks**: System designed with safe defaults
5. **Monitor Email Alerts**: Detailed reports sent automatically

### Key Files for Error Investigation

- `SILENT_FAILURES_FIXED.md`: Documents all silent failure fixes applied
- `ERROR_HANDLING_IMPLEMENTATION.md`: Detailed error handling architecture
- `core/error_handler.py`: Central error handling and categorization
- `core/exceptions.py`: Custom exception definitions with context

### Testing Error Handling

```python
# Test strategy error handling
from the_alchemiser.core.trading.strategy_engine import NuclearStrategyEngine
engine = NuclearStrategyEngine()

try:
    engine._get_14_day_volatility('INVALID_SYMBOL', {})
except IndicatorCalculationError as e:
    print(f"SUCCESS: Proper exception: {e}")
```

---

This README is for personal reference and intentionally omits marketing material.
