# Alchemiser Copilot Instructions

## Overview
The Alchemiser is a sophisticated multi-strategy quantitative trading system built with modern Python practices and Domain-Driven Design (DDD) architecture, deployed as AWS Lambda functions.

### Core Architecture (Layered DDD)
- **Domain Layer** (`the_alchemiser/domain/`): Pure business logic, strategy engines (Nuclear, TECL, KLM), interfaces, and domain types
- **Services Layer** (`the_alchemiser/services/`): Business logic orchestration and enhanced services facade
- **Infrastructure Layer** (`the_alchemiser/infrastructure/`): External integrations (Alpaca API, AWS services, WebSocket streaming)  
- **Application Layer** (`the_alchemiser/application/`): Trading orchestration, smart execution, portfolio rebalancing
- **Interface Layer** (`the_alchemiser/interface/`): Rich CLI with Typer, email notifications, dashboard utilities

### Key Components & Data Flow
- **AlpacaManager** (`services/alpaca_manager.py`): Central repository implementation for all Alpaca API operations
- **TradingServiceManager** (`services/enhanced/trading_service_manager.py`): Facade providing unified access to OrderService, PositionService, MarketDataService, AccountService
- **Multi-Strategy Engine** (`domain/strategies/`): Nuclear (sector rotation), TECL (volatility), KLM (ML ensemble)
- **Smart Execution** (`application/smart_execution.py`): Progressive orders, spread analysis, market impact optimization
- **Portfolio Rebalancer** (`application/portfolio_rebalancer/`): Target allocation computation and trade sizing
- **Modular CLI Architecture** (`interface/cli/`): Clean entry point with separated concerns
  - **Main Entry Point** (`main.py`): TradingSystem orchestrator (180 lines, 75% reduction from original)
  - **SignalAnalyzer** (`signal_analyzer.py`): Dedicated signal analysis and display logic
  - **TradingExecutor** (`trading_executor.py`): Dedicated trading execution with comprehensive error handling
- **CLI Commands**: `signal` (analysis only), `trade` (execution), `status` (account), `deploy` (AWS), `validate-indicators`

## Development Standards

### Python Environment (CRITICAL)
- **Always use Poetry**: ALL Python commands must use `poetry run` prefix
- **Never use bare python**: Use `poetry run python` instead of `python`
- **Virtual environment**: Poetry automatically manages the virtual environment
- **Dependencies**: Use `poetry add` for new dependencies, `poetry install` for setup

### Type Safety (Required)
- **100% mypy compliance**: Every function must have type annotations
- **Strict typing**: Use `from typing import` for complex types, prefer Protocol over ABC
- **Domain types**: Use types from `the_alchemiser.domain.types` for business objects
- **Return annotations**: Always specify return types, use `None` explicitly

### Error Handling Patterns
**Never fail silently** - Always use proper exception handling:

```python
from the_alchemiser.services.error_handler import TradingSystemErrorHandler
from the_alchemiser.services.exceptions import StrategyExecutionError

def risky_trading_operation():
    try:
        # Your trading logic
        return execute_trade()
    except Exception as e:
        error_handler = TradingSystemErrorHandler()
        error_handler.handle_error(
            error=e,
            component="ComponentName.method_name",
            context="specific_operation_description",
            additional_data={"symbol": "AAPL", "qty": 100}
        )
        raise StrategyExecutionError(f"Trading operation failed: {e}") from e
```

**Error Categories**: CRITICAL, TRADING, DATA, STRATEGY, CONFIGURATION, NOTIFICATION, WARNING

### Architecture Patterns

**Repository Pattern** (Domain interfaces with infrastructure implementations):
```python
from the_alchemiser.domain.interfaces import TradingRepository, MarketDataRepository
from the_alchemiser.services.alpaca_manager import AlpacaManager

# AlpacaManager implements all repository interfaces
alpaca_manager = AlpacaManager(api_key, secret_key, paper=True)
# Use through enhanced services for business operations
```

**Service Facade Pattern** (TradingServiceManager):
```python
from the_alchemiser.services.enhanced import TradingServiceManager

# Single entry point for all trading operations
trading_manager = TradingServiceManager(api_key, secret_key, paper=True)
order_result = trading_manager.execute_smart_order("AAPL", 10, "buy")
positions = trading_manager.get_all_positions()
```

**Strategy Engine Pattern** (Multi-strategy execution):
```python
from the_alchemiser.domain.strategies import StrategyManager

# Strategies run independently and merge signals
strategy_manager = StrategyManager()
nuclear_signals = strategy_manager.nuclear_strategy.generate_signals()
tecl_signals = strategy_manager.tecl_strategy.generate_signals()
```

**Dependency Injection**: Inject dependencies via constructors, prefer composition over inheritance

## Code Style and Quality

### Formatting (Black + Ruff)
- **Line length**: 100 characters maximum
- **Import organization**: Ruff automatically sorts imports
- **Format command**: `make format` or `black . && ruff check --fix .`
- **Type checking**: `mypy the_alchemiser/` must pass with no errors

### Naming Conventions
- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private attributes**: `_leading_underscore`
- **Domain objects**: End with descriptive suffix (`OrderRequest`, `PositionInfo`)

### Module Placement Rules
- **Pure business logic**: `domain/` layer
- **External API calls**: `infrastructure/` or `services/` layer  
- **Application workflows**: `application/` layer
- **User interfaces**: `interface/` layer
- **Shared utilities**: `utils/` package

### Documentation Management
- **Wiki Repository**: Use the `alchemiser-quant.wiki` workspace for all documentation
- **Architecture docs**: Create comprehensive guides in the wiki
- **API documentation**: Document interfaces and usage patterns in wiki
- **Deployment guides**: Step-by-step instructions in wiki format
- **Note**: The wiki appears as a separate git repository in the workspace but is linked to the main repo

## Testing Requirements

### Testing Framework (pytest + pytest-mock)
```python
def test_order_placement(mocker):
    # Use pytest-mock, not unittest.mock
    mock_trading = mocker.Mock()
    mock_trading.place_market_order.return_value = "ORDER123"
    
    service = OrderService(mock_trading)
    order_id = service.place_market_order("AAPL", "buy", 1.0)
    
    assert order_id == "ORDER123"
    mock_trading.place_market_order.assert_called_once()
```

### Test Organization
- **Unit tests**: `tests/unit/` - Fast, isolated, mocked dependencies
- **Integration tests**: `tests/integration/` - Component interactions
- **Infrastructure tests**: `tests/infrastructure/` - AWS/deployment validation
- **Fixtures**: `tests/conftest.py` provides shared mocks and test data

### Mock Strategy
- **Never call real APIs** in tests - use mocks exclusively
- **Use global fixtures**: `mock_alpaca_client`, `mock_aws_clients` from `conftest.py`
- **Test data builders**: Use `TestDataBuilder` from `tests/utils/mocks.py`

## CLI and Workflow

### Development Commands
```bash
# Setup (Poetry-based - ALWAYS REQUIRED)
poetry install                   # Install dependencies
poetry shell                     # Activate virtual environment
make dev                         # Install with dev dependencies

# Quality & Testing (ALL commands use poetry run)
make format                      # Black + Ruff formatting
make lint                        # Linting, type checking, security
make test                        # Run pytest with coverage reporting
poetry run pytest tests/unit/   # Fast unit tests only
poetry run pytest tests/integration/  # Integration tests
poetry run mypy the_alchemiser/ # Type checking standalone

# Trading Operations (CLI - ALL use poetry run)
poetry run alchemiser signal               # Strategy analysis (no trading)
poetry run alchemiser trade                # Paper trading execution
poetry run alchemiser trade --live         # Live trading (requires confirmation)
poetry run alchemiser status               # Account positions and P&L
poetry run alchemiser deploy               # Deploy to AWS Lambda
poetry run alchemiser validate-indicators  # Validate strategy indicators

# AWS Deployment
sam build --cached              # Build Lambda deployment package
sam deploy --guided             # Deploy with guided configuration
aws logs tail /aws/lambda/the-alchemiser-v2-lambda --follow  # Monitor logs

# Documentation (Use Wiki Workspace)
# All documentation should be written in the alchemiser-quant.wiki workspace
# The wiki presents as a separate git repo but is linked to the main repository

# Testing and Development (ALWAYS use poetry run)
poetry run python -c "import the_alchemiser; print('Import test')"
poetry run python test_script.py
poetry run python -m the_alchemiser.main  # Run main module
```

### CLI Architecture (Rich + Typer)
- **Built with Typer**: Modern CLI framework with automatic help generation and type validation
- **Rich formatting**: Console output with progress bars, tables, panels, and styled text using Rich library  
- **Dashboard utilities**: (`interface/cli/dashboard_utils.py`) Format positions, P&L, account status
- **Signal display**: (`interface/cli/signal_display_utils.py`) Strategy signal visualization with color coding
- **Error handling**: Comprehensive error display with suggested actions and formatted stack traces
- **Safety features**: Multiple confirmation prompts for live trading, clear paper/live mode indicators

## Critical Patterns

### Trading Service Usage (Always use TradingServiceManager)
```python
from the_alchemiser.services.enhanced import TradingServiceManager

# Initialize with environment detection
trading_manager = TradingServiceManager(api_key, secret_key, paper=True)

# Smart order execution with validation
result = trading_manager.execute_smart_order(
    symbol="AAPL", 
    quantity=10, 
    side="buy",
    order_type="market"
)

# Enhanced position management
positions = trading_manager.get_all_positions()
portfolio_value = trading_manager.get_portfolio_value()
```

### Money and Precision
```python
from decimal import Decimal

# Always use Decimal for financial calculations
portfolio_value = Decimal("100000.00")
position_size = portfolio_value * Decimal("0.1")
```

### Strategy Implementation Pattern
```python
from the_alchemiser.domain.strategies import StrategyEngine

# Inherit from StrategyEngine for new strategies
class CustomStrategy(StrategyEngine):
    def generate_signals(self) -> Dict[str, Any]:
        # Implement strategy logic
        return {
            "signal": "BUY",
            "confidence": 0.8,
            "target_allocation": 0.25,
            "reasoning": "Custom indicator triggered"
        }
    
    def validate_signals(self, signals: Dict[str, Any]) -> bool:
        # Implement validation logic
        return signals.get("confidence", 0) > 0.5
```

### AWS Lambda Integration Pattern
```python
# lambda_handler.py entry point
from the_alchemiser.main import main as trading_main

def lambda_handler(event: dict, context) -> dict:
    """AWS Lambda handler with proper error handling and logging"""
    try:
        result = trading_main()
        return {"statusCode": 200, "body": result}
    except Exception as e:
        # Error handler automatically sends email notifications
        return {"statusCode": 500, "body": str(e)}
```

### Configuration Management
```python
from the_alchemiser.infrastructure.config import load_settings

# Pydantic-based settings with environment variable support
settings = load_settings()
paper_trading = settings.alpaca.paper_trading
cash_reserve = settings.alpaca.cash_reserve_pct
```

## Testing & Quality Requirements

### Test Structure & Organization
- **Unit tests**: `tests/unit/` - Fast, isolated, mocked dependencies (pytest-mock)
- **Integration tests**: `tests/integration/` - Component interactions with real data flows
- **Infrastructure tests**: `tests/infrastructure/` - AWS/deployment validation
- **Performance tests**: `tests/performance/` - Latency and throughput validation
- **Property tests**: `tests/property/` - Hypothesis-based property testing
- **Fixtures**: `tests/conftest.py` provides shared mocks, test data builders

### Critical Testing Patterns
```python
def test_trading_operation(mocker):
    # Use pytest-mock, not unittest.mock
    mock_alpaca = mocker.Mock()
    mock_alpaca.place_market_order.return_value = "ORDER123"
    
    # Test through service layer, not direct repository
    trading_manager = TradingServiceManager("key", "secret", paper=True)
    trading_manager.alpaca_manager = mock_alpaca
    
    result = trading_manager.place_market_order("AAPL", 10, "buy")
    assert result["order_id"] == "ORDER123"

# Run tests with: poetry run pytest tests/unit/test_file.py
# Run all tests with: poetry run pytest
```

## Security and Environment Management

### Environment Variables (Required for all operations)
```bash
# Alpaca Trading API
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
PAPER_TRADING=true                # false for live trading

# AWS Infrastructure
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=eu-west-2             # Default deployment region

# Email notifications
EMAIL_RECIPIENT=your@email.com

# Optional: Advanced configuration
ALPACA__CASH_RESERVE_PCT=0.05    # 5% cash reserve
ALPACA__SLIPPAGE_BPS=5           # 5 basis points slippage allowance
LOGGING__LEVEL=INFO              # Logging verbosity
```

### Trading Mode Safety & Production Readiness
- **Default to paper trading**: All services initialize with `paper=True` unless explicitly overridden
- **Environment isolation**: Separate API keys and AWS accounts for paper vs live environments
- **Confirmation prompts**: CLI requires explicit `--live` flag and confirmation for live trading  
- **Error notifications**: Automatic email alerts for all error categories with detailed context
- **AWS Lambda deployment**: Production system runs as scheduled Lambda functions with dead letter queues
- **Monitoring**: CloudWatch logs, error tracking, and performance monitoring built-in

## Common Pitfalls to Avoid

1. **Silent failures**: Always raise proper exceptions with detailed context, never return `None` for failures
2. **Direct repository usage**: Use TradingServiceManager facade, not AlpacaManager directly in application code
3. **Untyped code**: Every function needs complete type annotations for mypy compliance (100% coverage required)
4. **Missing error handling**: All trading operations must use TradingSystemErrorHandler for consistency
5. **Float precision**: Use `Decimal` for all financial calculations, avoid float arithmetic
6. **Global state**: Use dependency injection through constructors, avoid global variables
7. **Strategy coupling**: Keep strategies independent - they should not call each other directly
8. **Test isolation**: Mock all external APIs in tests, use fixtures from `conftest.py`
9. **Forgetting Poetry**: ALWAYS use `poetry run` for Python commands - never use bare `python`
10. **Documentation in wrong place**: Use the `alchemiser-quant.wiki` workspace for documentation, not the main repo

