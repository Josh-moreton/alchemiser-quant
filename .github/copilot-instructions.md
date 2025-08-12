# Alchemiser Copilot Instructions

## Overview
The Alchemiser is a sophisticated multi-strategy quantitative trading system built with modern Python practices and clean architecture principles.

### Core Architecture (Layered DDD)
- **Domain Layer** (`the_alchemiser/domain/`): Core business logic, interfaces, and types
- **Services Layer** (`the_alchemiser/services/`): Business logic orchestration and enhanced services
- **Infrastructure Layer** (`the_alchemiser/infrastructure/`): External integrations (Alpaca, AWS)  
- **Application Layer** (`the_alchemiser/application/`): High-level workflows and trading engines
- **Interface Layer** (`the_alchemiser/interface/`): CLI, email notifications, and external APIs

### Key Components
- **AlpacaManager** (`services/alpaca_manager.py`): Unified Alpaca API client implementing all repository interfaces
- **TradingEngine** (`application/trading_engine.py`): Main trading orchestration with multi-strategy execution
- **Enhanced Services** (`services/enhanced/`): OrderService, PositionService, MarketDataService, AccountService
- **CLI Interface** (`interface/cli/`): Rich Typer-based CLI with commands: `signal`, `trade`, `status`, `deploy`
- **Error System** (`services/error_handler.py`): Comprehensive error categorization with email notifications

## Development Standards

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

**Repository Pattern** (Use domain interfaces):
```python
from the_alchemiser.domain.interfaces import TradingRepository

# Depend on abstractions, not implementations
def create_service(trading_repo: TradingRepository):
    return OrderService(trading_repo)
```

**Service Layer Pattern**:
```python
from the_alchemiser.services.enhanced import OrderService, TradingServiceManager

# Use enhanced services for business logic
order_service = OrderService(alpaca_manager)
order_id = order_service.place_market_order("AAPL", "buy", 1.0, validate_price=True)
```

**Dependency Injection**: Inject dependencies via constructors, avoid global instances

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
# Setup
make dev                          # Install dev dependencies
poetry install                    # Alternative setup

# Quality
make format                       # Black + Ruff formatting
make lint                         # Linting and type checking
make test                         # Run test suite with coverage
mypy the_alchemiser/             # Type checking

# Trading Operations
alchemiser signal                 # Generate strategy signals (analysis only)
alchemiser trade                  # Execute paper trading
alchemiser trade --live           # Execute live trading (requires confirmation)
alchemiser status                 # Show account status and positions
alchemiser deploy                 # Deploy to AWS Lambda
```

### CLI Architecture (Rich + Typer)
- **Built with Typer**: Modern CLI framework with automatic help generation
- **Rich formatting**: Console output with colors, tables, and progress indicators
- **Error handling**: Comprehensive error display with suggested actions
- **Safety features**: Confirmation prompts for live trading, clear mode indicators

## Critical Patterns

### Money and Precision
```python
from decimal import Decimal

# Always use Decimal for financial calculations
portfolio_value = Decimal("100000.00")
position_size = portfolio_value * Decimal("0.1")
```

### Market Data Handling
```python
from the_alchemiser.services.enhanced import MarketDataService

# Use enhanced services for data operations
market_data = MarketDataService(alpaca_manager)
price = market_data.get_current_price("AAPL", validate=True)
spread_info = market_data.analyze_spread("AAPL")
```

### Trading Execution
```python
from the_alchemiser.services.enhanced import TradingServiceManager

# Use TradingServiceManager for high-level operations
trading_manager = TradingServiceManager(api_key, secret_key, paper=True)
result = trading_manager.execute_smart_order("AAPL", 10, "buy", order_type="market")
```

### Configuration Management
```python
from the_alchemiser.infrastructure.config import load_settings

# Pydantic-based settings with environment variable support
settings = load_settings()
paper_trading = settings.alpaca.paper_trading
```

## Security and Environment

### Environment Variables
```bash
# Required for all operations
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
PAPER_TRADING=true                # false for live trading

# AWS Infrastructure
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1

# Email notifications
EMAIL_RECIPIENT=your@email.com
```

### Trading Mode Safety
- **Default to paper trading**: Always initialize with `paper=True` unless explicitly live
- **Environment isolation**: Separate API keys for paper vs live accounts
- **Confirmation prompts**: CLI requires explicit confirmation for live trading
- **Error notifications**: Automatic email alerts for all error categories

## Common Pitfalls to Avoid

1. **Silent failures**: Always raise proper exceptions, never return `None` without handling
2. **Global state**: Use dependency injection, avoid global variables
3. **Untyped code**: Every function needs type annotations for mypy compliance
4. **Direct API calls**: Use repository interfaces and enhanced services
5. **Bare except blocks**: Catch specific exceptions and handle appropriately
6. **Float precision**: Use `Decimal` for all financial calculations
7. **Missing error context**: Include component, context, and debugging data in error handling

