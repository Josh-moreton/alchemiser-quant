# The Alchemiser

Internal notes on how the trading bot is put together and how the pieces interact.

## Quick Start

### Environment Setup with direnv (Recommended)

1. **Install direnv**: `brew install direnv` (macOS) or see [direnv.net](https://direnv.net/)
2. **Configure your shell**: Add `eval "$(direnv hook zsh)"` to `~/.zshrc` (or bash equivalent)
3. **Set up the project**: `cp .envrc.template .envrc && direnv allow`
4. **Test**: `cd .. && cd the-alchemiser` - you should see "🔧 Environment activated"

Now your Python virtual environment and all project settings are automatically activated when you enter the directory!

### Manual Setup (Alternative)

If you prefer manual environment management:

```bash
source .venv/bin/activate
export PYTHONPATH="${PWD}:${PWD}/the_alchemiser:${PYTHONPATH}"
```

## System Architecture

### Layered DDD Architecture (Domain-Driven Design)

- **Domain Layer** (`the_alchemiser/domain/`): Pure business logic, strategy engines (Nuclear, TECL, KLM), interfaces, and domain types
- **Services Layer** (`the_alchemiser/services/`): Business logic orchestration and enhanced services facade
- **Infrastructure Layer** (`the_alchemiser/infrastructure/`): External integrations (Alpaca API, AWS services, WebSocket streaming)
- **Application Layer** (`the_alchemiser/application/`): Trading orchestration, smart execution, portfolio rebalancing
- **Interface Layer** (`the_alchemiser/interface/`): Modular CLI with clean separation of concerns

## Typed Domain System (V2)

We’re migrating to a strongly-typed, framework-free domain model with incremental rollout behind a feature flag. The goal is >95% precise typing, clearer boundaries, and safer refactors.

### Key Concepts
- Shared Kernel Value Objects (immutable): `Money`, `Percentage`, `Identifier` under `the_alchemiser/domain/shared_kernel/value_objects/`
- Trading Domain: Entities `Order`, `Position`, `Account`; Value Objects `Symbol`, `Quantity`, `OrderStatus` under `the_alchemiser/domain/trading/`
- Strategies Domain: `StrategySignal`, `Confidence`, `Alert` under `the_alchemiser/domain/strategies/value_objects/`
- Anti‑corruption Mappers: `the_alchemiser/application/mapping/` handles DTO ↔ Domain ↔ Infra translations
- Infra Adapters: Alpaca requests/responses mapped in `the_alchemiser/infrastructure/`; domain stays pure

### Enable the Typed Path

Set the feature flag to exercise the typed slices end‑to‑end:

```bash
export TYPES_V2_ENABLED=1   # truthy values: 1, true, yes, on
```

### What’s Migrated (behind the flag)
- Portfolio value parity via `TradingServiceManager`
- Enriched positions summary and CLI rendering (status)
- Enriched account summary and CLI status integration
- Order placement (market and limit): typed request build + domain `Order` mapping
- Open orders retrieval mapped to domain `Order`
- StrategySignal typed mapping through Execution and CLI

### Contributor Notes
- Domain purity: no framework imports (no Pydantic, requests, logging) in `the_alchemiser/domain/**`
- Use `@dataclass(frozen=True)` for value objects; entities encapsulate behavior
- Keep Pydantic DTOs in `the_alchemiser/interfaces/schemas/`
- Place all boundary mapping in `the_alchemiser/application/mapping/`
- Use `Decimal` for all financial/quantity values; normalize in mappers
- Prefer `Protocol` for repository/service interfaces under `domain/**/protocols/`; implemented in `infrastructure/` or `services/`

### Testing the Typed Path
- Add parity tests for flag ON vs OFF where behavior should be identical
- Unit test mappers with realistic fixtures; mock external APIs (pytest‑mock)
- CI runs mypy across the codebase; value objects and entities must be fully typed

### Entry Point and CLI Architecture

- **Main Entry Point** (`main.py`): Clean, focused entry point (180 lines) with `TradingSystem` orchestrator
- **Signal Analyzer** (`interface/cli/signal_analyzer.py`): Dedicated signal analysis and display logic
- **Trading Executor** (`interface/cli/trading_executor.py`): Dedicated trading execution with comprehensive error handling
- **Dependency Injection**: Default DI mode with `--legacy` flag support for traditional initialization

### Configuration and Settings

- `the_alchemiser.infrastructure.config` uses Pydantic settings models to load configuration from environment variables and `.env` files.

### Data Layer

- `the_alchemiser.infrastructure.data_providers.UnifiedDataProvider` unifies Alpaca REST and WebSocket access to provide account details, quotes and historical data.

### Strategy Layer

- Strategy engines live in `the_alchemiser.domain.strategies`.
- `MultiStrategyManager` instantiates enabled strategies and keeps per‑strategy position tracking and allocation.

### Execution Layer

- `TradingEngine` orchestrates the full trading cycle: it gathers strategy signals, invokes `PortfolioRebalancer` to compute target allocations and delegates order placement to `SmartExecution`.
- `ExecutionManager` drives multi‑strategy execution; enhanced services provide unified access to trading operations.

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
    - Typed Domain V2 gate: keep domain free of frameworks; all financial values are `Decimal`.
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
- ✅ **Typed Domain V2**: Prefer domain value objects/entities over untyped dicts; route new work via mappers

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
├── core/                          # Legacy/core logic (being migrated to domain/)
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

# New typed domain directories (incremental rollout)
the_alchemiser/domain/
├── shared_kernel/
│   └── value_objects/             # Money, Percentage, Identifier
├── trading/
│   ├── entities/                  # Order, Position, Account
│   ├── value_objects/             # Symbol, Quantity, OrderStatus
│   └── protocols/                 # Repository interfaces
└── strategies/
    └── value_objects/             # StrategySignal, Confidence, Alert

the_alchemiser/application/mapping/  # Anti‑corruption mappers (DTO ↔ Domain ↔ Infra)
the_alchemiser/interfaces/schemas/   # Pydantic DTOs for I/O
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

## Business Logic and Data Flow

### Strategy Execution Pipeline

**Multi-Strategy Coordination** (`core/trading/strategy_manager.py`):

1. **Signal Generation**: Each strategy (Nuclear, TECL) generates independent signals
2. **Portfolio Allocation**: Strategies are allocated based on configured weights
3. **Signal Consolidation**: Multiple strategy signals merged into target portfolio
4. **Attribution Tracking**: Each position tracked back to originating strategy

**Key Strategy Patterns**:

- **Nuclear Strategy**: Bear/bull market detection with uranium mining focus
- **TECL Strategy**: Technology leverage with volatility protection
- **Market Regime Detection**: SPY 200-day MA analysis for bull/bear classification
- **Volatility-Based Allocation**: Inverse volatility weighting for risk management

### Order Execution Flow

**Smart Execution Pipeline** (`execution/smart_execution.py`):

1. **Market Timing Assessment**: 9:30-9:35 ET special handling
2. **Aggressive Marketable Limits**: Ask+1¢ for buys, bid-1¢ for sells
3. **Re-pegging Sequence**: 2-3 second timeouts with price updates
4. **Market Order Fallback**: Execution certainty for critical fills

**Professional Order Strategy**:

- Better Orders execution methodology
- Spread analysis and timing optimization
- Pre-market condition assessment
- Fractionable asset handling with fallbacks

### Data Provider Architecture

**Unified Data Access** (`core/data/data_provider.py`):

- **Real-time Priority**: WebSocket data preferred over REST
- **Automatic Fallbacks**: REST API backup for real-time failures
- **Historical Fallbacks**: Recent price history when quotes unavailable
- **Caching Layer**: Intelligent caching with TTL for performance

**Data Sources**:

- Alpaca REST API (primary)
- Alpaca WebSocket (real-time)
- Historical price fallback
- Technical indicator calculations

### Risk Management System

**Position Validation** (`execution/alpaca_client.py`):

- **Buying Power Checks**: Prevent overleverage on buy orders
- **Position Validation**: Ensure sufficient holdings for sell orders
- **Fractionability Handling**: Automatic conversion for non-fractional assets
- **Asset Type Detection**: ETF vs stock handling differences

**Portfolio Constraints**:

- Maximum position sizes per strategy
- Cash allocation minimums (5% minimum cash)
- Volatility-based position sizing
- Conservative fallbacks during calculation errors

### Performance Tracking and Attribution

**Strategy Attribution** (`tracking/strategy_order_tracker.py`):

- Per-strategy order tracking
- Position attribution to originating signals
- P&L calculation by strategy
- Historical performance analysis

**Reporting Pipeline**:

- Real-time execution summaries
- Daily P&L archiving
- Email reporting with rich formatting
- Dashboard data generation for web interface

### Configuration and Environment Management

**Environment-Specific Settings**:

```python
# Paper trading vs live trading
PAPER_TRADING=true  # Safe default
ALPACA_API_KEY=your_paper_key
ALPACA_SECRET_KEY=your_paper_secret

# Live trading (production)
PAPER_TRADING=false
ALPACA_API_KEY=your_live_key
ALPACA_SECRET_KEY=your_live_secret
```

**Key Configuration Points**:

- Trading mode (paper/live) isolation
- Strategy allocation weights
- Email notification settings
- Risk management parameters
- Market hours enforcement

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
make dev                            # install with dev dependencies
make format                         # run black + ruff formatting
make lint                          # run flake8, mypy, security checks
make test                          # run pytest with coverage

# Modern CLI (DI-first architecture)
alchemiser signal                  # strategy analysis (DI mode, default)
alchemiser signal --legacy         # strategy analysis (legacy mode)
alchemiser trade                   # paper trading (DI mode)
alchemiser trade --live            # live trading (DI mode)
alchemiser trade --ignore-market-hours  # override market hours
alchemiser status                  # account status and positions
alchemiser deploy                  # deploy to AWS Lambda
```

Tip: to review typed behavior via CLI, export `TYPES_V2_ENABLED=1` and run:

```bash
poetry run alchemiser status -v
poetry run alchemiser trade --ignore-market-hours -v  # paper mode by default
```

## Development Workflow for AI Agents

### Local Development Setup

```bash
# 1. Install dependencies
poetry install

# 2. Set up environment
cp .env.example .env
# Edit .env with your Alpaca paper trading credentials

# 3. Run type checking
poetry run mypy the_alchemiser/

# 4. Format code
poetry run black the_alchemiser/
poetry run ruff the_alchemiser/

# 5. Run tests
poetry run pytest

# 6. Test strategies locally
poetry run alchemiser bot --paper
```

### Common Development Tasks

**Adding New Strategies**:

1. Create strategy engine in `core/trading/`
2. Implement required methods: `get_signal()`, `get_reasoning()`
3. Add to `StrategyType` enum
4. Register in `MultiStrategyManager`
5. Add tests and type hints

**Debugging Order Execution**:

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test individual order placement
from the_alchemiser.execution.smart_execution import SmartExecution
executor = SmartExecution(trading_client, data_provider)
order_id = executor.place_order("AAPL", 10, OrderSide.BUY)
```

**Testing Error Handling**:

```python
# Test specific error scenarios
from the_alchemiser.core.error_handler import TradingSystemErrorHandler
from the_alchemiser.core.exceptions import StrategyExecutionError

try:
    # Simulate error condition
    raise StrategyExecutionError("Test error", strategy_name="test")
except Exception as e:
    handler = TradingSystemErrorHandler()
    handler.handle_error(e, "test_component", "test_context")
```

### Code Review Checklist for AI Agents

**Type Safety**:

- ✅ All function parameters have type hints
- ✅ Return types specified for all functions
- ✅ No `Any` types unless absolutely necessary
- ✅ Protocols used for dependency injection

**Error Handling**:

- ✅ Custom exceptions raised instead of returning `None`
- ✅ Error context provided in exception messages
- ✅ Conservative fallbacks implemented where appropriate
- ✅ Error handler integration for critical operations

**Code Quality**:

- ✅ Functions are single-purpose and well-named
- ✅ No magic numbers (use constants or configuration)
- ✅ Comprehensive docstrings for public methods
- ✅ Logging at appropriate levels (DEBUG, INFO, WARNING, ERROR)

**Testing Requirements**:

- ✅ Unit tests for business logic
- ✅ Error condition testing
- ✅ Mock external dependencies (Alpaca API)
- ✅ Integration tests for critical paths

### Operational Knowledge

**Paper Trading vs Live Trading**:

- Paper trading uses separate Alpaca account and API keys
- All order execution is simulated but follows real market data
- Switch via `PAPER_TRADING` environment variable
- Live trading requires careful validation and testing

**Market Hours and Timing**:

- Regular hours: 9:30 AM - 4:00 PM ET
- Pre-market: 4:00 AM - 9:30 AM ET
- After-hours: 4:00 PM - 8:00 PM ET
- System can trade outside regular hours if configured

**Strategy Allocation Management**:

```python
# Configure strategy weights
strategy_allocations = {
    StrategyType.NUCLEAR: 0.6,  # 60% nuclear strategy
    StrategyType.TECL: 0.4      # 40% TECL strategy
}
```

**Performance Monitoring**:

- Daily P&L archived in S3
- Strategy attribution tracked per order
- Email reports sent after each execution
- Dashboard data updated in real-time

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

## Key Files Reference for AI Agents

### Core Trading Logic

- **`main.py`**: Entry point for strategy execution with comprehensive error handling
- **`lambda_handler.py`**: AWS Lambda wrapper with enhanced error reporting
- **`cli.py`**: Command-line interface for local testing and debugging

### Configuration and Settings

- **`core/config.py`**: Pydantic-based settings with environment variable support
- **`core/exceptions.py`**: Custom exception hierarchy for proper error categorization
- **`core/error_handler.py`**: Centralized error handling and email notification system

### Strategy Implementation

- **`core/trading/strategy_manager.py`**: Multi-strategy coordination and allocation
- **`core/trading/strategy_engine.py`**: Nuclear strategy with bear/bull market detection
- **`core/trading/tecl_strategy_engine.py`**: TECL technology strategy with volatility protection

### Order Execution

- **`execution/trading_engine.py`**: Main trading orchestration and portfolio management
- **`execution/smart_execution.py`**: Professional order execution with Better Orders methodology
- **`execution/alpaca_client.py`**: Direct Alpaca API client with validation and fallbacks
- **`execution/portfolio_rebalancer.py`**: Sell-then-buy rebalancing with attribution tracking

### Data and Market Access

- **`core/data/data_provider.py`**: Unified Alpaca REST/WebSocket data access with caching
- **`utils/price_fetching_utils.py`**: Price retrieval with multiple fallback strategies
- **`utils/market_timing_utils.py`**: Market hours detection and execution timing

### Monitoring and Tracking

- **`tracking/strategy_order_tracker.py`**: Per-strategy order and P&L attribution
- **`utils/portfolio_pnl_utils.py`**: Portfolio performance calculation utilities
- **`core/ui/email/`**: Email templates and notification system

### Development and Documentation

- **`pyproject.toml`**: Poetry dependencies, mypy, black, and ruff configuration
- **`template.yaml`**: AWS CloudFormation infrastructure with retry policies
- **`Makefile`**: Development workflow automation (format, lint, test)

### Important Constants and Enums

- **`StrategyType`**: Enum for strategy identification (NUCLEAR, TECL)
- **`OrderSide`**: Buy/sell order direction
- **`ErrorCategory`**: Error classification for proper handling

### Environment Variables Required

```bash
# Alpaca API (separate keys for paper/live)
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
PAPER_TRADING=true  # false for live trading

# Email notifications
EMAIL_RECIPIENT=your_email@domain.com
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret

# Optional configurations
IGNORE_MARKET_HOURS=false
VALIDATE_BUYING_POWER=true
```

### Critical Dependencies to Monitor

- **`alpaca-py`**: Primary trading API client
- **`pydantic`**: Configuration and data validation
- **`rich`**: Terminal formatting and progress display
- **`boto3`**: AWS services (S3, SQS, SES)
- **`pandas`**: Data analysis and technical indicators

---

This README is for personal reference and intentionally omits marketing material.
